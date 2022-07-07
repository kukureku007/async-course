from typing import List
from os import listdir
import asyncio
import curses
from itertools import cycle
from random import choice, randint, uniform
from time import sleep

from phisics import update_speed

SPEED = 5
# 0 for disable borders
BORDERS = 0
TIC_TIMEOUT = 0.1
STARS = '+*.:'
STARS_NUM = 100
# через сколько тиков должен появляться новый мусор
NEW_GARBAGE_TICS_TIMEOUT = 10
MIN_GARBAGE_SPEED = 0.3
MAX_GARBAGE_SPEED = 1

FRAMES_DIR = 'lesson1/frames'
GARBAGE_FRAMES = [
    f'{FRAMES_DIR}/garbage/{name}' for name in listdir(
        f'{FRAMES_DIR}/garbage/'
    )
]
SPACESHIP_FRAMES = [
    f'{FRAMES_DIR}/spaceship/{name}' for name in listdir(
        f'{FRAMES_DIR}/spaceship/'
    )
]

SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258


def cycle_with_repeat(iterable, repeat=1):
    """
    generator that returns items from itertools.cycle repeatedly
    e.g. [a,b,c], repeat=2 -> a,a,b,b,c,c,a,a,b,...
    """
    for item in cycle(iterable):
        for _ in range(repeat):
            yield item


def read_controls(canvas, row_speed, column_speed):
    """Read keys pressed and returns tuple witl controls state."""

    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 1

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -1

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True

    return (
        *update_speed(
            row_speed, column_speed,
            rows_direction, columns_direction,
            row_speed_limit=SPEED,
            column_speed_limit=SPEED
        ),
        space_pressed)


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


async def asleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def fire(canvas, start_row, start_column,
               rows_speed=-1, columns_speed=0):
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

    while BORDERS < row < max_row and BORDERS < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate_spaceship(coroutines: List, canvas, start_row, start_column, frames):
    frame_rows, frame_columns = get_frame_size(frames[0])
    max_row, max_column = canvas.getmaxyx()

    current_row = start_row - (frame_rows // 2)
    current_column = start_column - (frame_columns // 2)

    rows_speed = columns_speed = 0

    for frame in cycle_with_repeat(frames, repeat=2):
        # repeat - speed of ship animation
        rows_speed, columns_speed, action_fire = read_controls(
            canvas, rows_speed, columns_speed
        )

        current_row = validate_rows(
            current_row+rows_speed,
            BORDERS,
            max_row-frame_rows-BORDERS
        )
        current_column = validate_columns(
            current_column+columns_speed,
            BORDERS,
            max_column-frame_columns-BORDERS
        )

        draw_frame(canvas, current_row, current_column, frame)
        if action_fire:
            coroutines.append(
                fire(canvas, current_row, current_column + frame_columns // 2)
            )

        await asyncio.sleep(0)
        draw_frame(canvas, current_row, current_column, frame, negative=True)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom.
    Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, BORDERS)
    column = min(column, columns_number - 1 - BORDERS)

    row = BORDERS

    while row < rows_number-1:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed


async def blink(canvas, row, column, symbol='*'):
    await asleep(randint(0, 25))
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await asleep(20)

        canvas.addstr(row, column, symbol)
        await asleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await asleep(5)

        canvas.addstr(row, column, symbol)
        await asleep(3)


async def fill_orbit_with_garbage(
    coroutines: List, canvas, garbage_frames, max_column
):
    while True:
        for _ in range(NEW_GARBAGE_TICS_TIMEOUT):
            await asyncio.sleep(0)
        coroutines.append(fly_garbage(
                canvas,
                column=randint(BORDERS, max_column-1-BORDERS),
                garbage_frame=choice(garbage_frames),
                speed=uniform(MIN_GARBAGE_SPEED, MAX_GARBAGE_SPEED)
            ))


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
            randint(BORDERS, max_row-1-BORDERS),
            randint(BORDERS, max_column-1-BORDERS),
            choice(STARS)
        ))

    # coroutines.append(fire(canvas, max_row // 2, max_column // 2))
    garbage_frames = get_frames(GARBAGE_FRAMES)

    coroutines.append(
        fill_orbit_with_garbage(coroutines, canvas, garbage_frames, max_column)
    )

    coroutines.append(animate_spaceship(
        coroutines,
        canvas,
        max_row // 2,
        max_column // 2,
        get_frames(SPACESHIP_FRAMES)
    ))

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()

        sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
