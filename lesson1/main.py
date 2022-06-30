import asyncio
import time
import curses
import random
import itertools

SPEED = 5
# 0 for disable borders
BORDERS = 1
TIC_TIMEOUT = 0.1
STARS = '+*.:'
STARS_NUM = 100
SPACESHIP_FRAMES = (
    'lesson1/frames/rocket_frame_1.txt',
    'lesson1/frames/rocket_frame_2.txt'
)
SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258


def read_controls(canvas, speed=1):
    """Read keys pressed and returns tuple witl controls state."""

    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -speed

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = speed

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = speed

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -speed

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True

    return rows_direction, columns_direction, space_pressed


def draw_frame(canvas, start_row, start_column, text, negative=False):
    """
    Draw multiline text fragment on canvas, erase text instead
    of drawing if negative=True is specified.
    """

    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue

        if row >= rows_number:
            break

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue

            if column >= columns_number:
                break

            if symbol == ' ':
                continue

            # Check that current position it is not in a lower right corner
            # of the window
            # Curses will raise exception in that case. Don`t ask why…
            # https://docs.python.org/3/library/curses.html#curses.window.addch
            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


def get_frame_size(text):
    """
    Calculate size of multiline text fragment,
    return pair — number of rows and colums.
    """

    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


def get_frames(file_names):
    frames = []
    for file_name in file_names:
        with open(file_name, 'r', encoding='utf-8') as file:
            frames.append(file.read())
    return frames


def validate_rows(rows, rows_min, rows_max):
    if rows < rows_min:
        return rows_min
    if rows > rows_max:
        return rows_max
    return rows


def validate_columns(columns, columns_min, columns_max):
    if columns < columns_min:
        return columns_min
    if columns > columns_max:
        return columns_max
    return columns


async def animate_spaceship(canvas, start_row, start_column):
    frames = get_frames(SPACESHIP_FRAMES)
    frame_rows, frame_columns = get_frame_size(frames[0])
    max_row, max_column = canvas.getmaxyx()

    current_row = start_row - (frame_rows // 2)
    current_column = start_column - (frame_columns // 2)

    frames_cycle = itertools.cycle(frames)
    frame = next(frames_cycle)
    frames_count = 0

    while True:
        rows_direction, columns_direction, _ = read_controls(canvas, SPEED)

        current_row = validate_rows(
            current_row+rows_direction,
            BORDERS,
            max_row-frame_rows-BORDERS
        )
        current_column = validate_columns(
            current_column+columns_direction,
            BORDERS,
            max_column-frame_columns-BORDERS
        )

        # Анимация происходит через каждые два кадра
        if frames_count >= 2:
            frame = next(frames_cycle)
            frames_count = 0

        draw_frame(canvas, current_row, current_column, frame)
        await asyncio.sleep(0)
        draw_frame(canvas, current_row, current_column, frame, negative=True)
        frames_count += 1


async def fire(canvas, start_row, start_column,
               rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1 - BORDERS, columns - 1 - BORDERS

    curses.beep()

    while 1 < row < max_row and 1 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, symbol='*'):
    for _ in range(random.randint(0, 25)):
        await asyncio.sleep(0)
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


def draw(canvas):
    curses.curs_set(False)
    if BORDERS:
        canvas.border()
    canvas.nodelay(True)

    max_row, max_column = canvas.getmaxyx()
    coroutines = []

    for _ in range(STARS_NUM):
        coroutines.append(blink(
            canvas,
            random.randint(BORDERS, max_row-1-BORDERS),
            random.randint(BORDERS, max_column-1-BORDERS),
            random.choice(STARS)
        ))

    coroutines.append(fire(canvas, max_row // 2, max_column // 2))
    coroutines.append(animate_spaceship(canvas, max_row // 2, max_column // 2))

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()

        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
