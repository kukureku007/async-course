from typing import List
import uuid
from os import listdir
import asyncio
import curses
from random import choice, randint, uniform

from obstacles import Obstacle, show_obstacles
from utils import (
                  cycle_with_repeat,
                  validate_value,
                  get_garbage_delay_tics
                  )
from curses_tools import get_frame_size, read_controls, draw_frame, get_frames
from explosion import explode

from config import (
    GOD_MODE,
    DEBUG,
    DEBUG_YEAR,
    SPEED,
    BORDERS,
    TIC_TIMEOUT,
    STARS,
    STARS_NUM,
    PHRASES,
    MIN_GARBAGE_SPEED,
    MAX_GARBAGE_SPEED,
    FRAMES_DIR
)


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
GAME_OVER_FRAME = get_frames((f'{FRAMES_DIR}/legends/gameover.txt',))

coroutines = []
obstacles: List[Obstacle] = []

obstacles_in_last_collisions: List[Obstacle] = []
obstacles_in_last_collisions: set = set()
year = DEBUG_YEAR if DEBUG else 1957
loop = asyncio.get_event_loop()


async def year_count():
    global year
    while True:
        await asyncio.sleep(15 * TIC_TIMEOUT)
        year += 1


async def fire(canvas, start_row, start_column,
               rows_speed=-2, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(TIC_TIMEOUT)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(TIC_TIMEOUT)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1 - BORDERS, columns - 1 - BORDERS

    curses.beep()

    while BORDERS < row < max_row and BORDERS < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(TIC_TIMEOUT)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed

        for obstacle in obstacles:
            if obstacle.has_collision(
                row, column
            ):
                obstacles_in_last_collisions.add(obstacle)
                return


async def game_over(canvas):
    frame_rows, frame_columns = get_frame_size(*GAME_OVER_FRAME)
    max_row, max_column = canvas.getmaxyx()
    while True:
        draw_frame(
            canvas,
            (max_row - frame_rows) // 2,
            (max_column - frame_columns) // 2,
            *GAME_OVER_FRAME
        )
        await asyncio.sleep(0.1)


async def animate_spaceship(
    canvas, start_row, start_column, frames
):
    frame_rows, frame_columns = get_frame_size(frames[0])
    max_row, max_column = canvas.getmaxyx()

    current_row = start_row - (frame_rows // 2)
    current_column = start_column - (frame_columns // 2)

    rows_speed = columns_speed = 0

    for frame in cycle_with_repeat(frames, repeat=2):
        rows_speed, columns_speed, action_fire = read_controls(
            canvas, rows_speed, columns_speed, SPEED
        )

        current_row = validate_value(
            current_row+rows_speed,
            BORDERS,
            max_row-frame_rows-BORDERS
        )
        current_column = validate_value(
            current_column+columns_speed,
            BORDERS,
            max_column-frame_columns-BORDERS
        )

        draw_frame(canvas, current_row, current_column, frame)
        if action_fire and (year > 2019 or GOD_MODE):
            loop.create_task(
                fire(canvas, current_row, current_column + frame_columns // 2)
            )
        await asyncio.sleep(TIC_TIMEOUT)
        draw_frame(canvas, current_row, current_column, frame, negative=True)

        for obstacle in obstacles:
            if obstacle.has_collision(
                current_row, current_column,
                frame_rows, frame_columns
            ) and not GOD_MODE:
                obstacles_in_last_collisions.add(obstacle)
                await explode(
                    canvas,
                    current_row + frame_rows // 2,
                    current_column + frame_columns // 2
                )
                loop.create_task(game_over(canvas))
                return


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom.
    Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, BORDERS)
    column = min(column, columns_number - 1 - BORDERS)

    row = BORDERS

    rows_size, columns_size = get_frame_size(garbage_frame)

    obstacle = Obstacle(
        row,
        column,
        rows_size,
        columns_size,
        uid=str(uuid.uuid4())
    )

    obstacles.append(obstacle)

    while row < rows_number-1:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(TIC_TIMEOUT)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
        if obstacle in obstacles_in_last_collisions:
            obstacles_in_last_collisions.remove(obstacle)
            await explode(
                canvas,
                row + rows_size // 2,
                column + columns_size // 2
            )
            break
        obstacle.row = row
    obstacles.remove(obstacle)


async def blink(canvas, row, column, symbol='*'):
    await asyncio.sleep(randint(0, 25) * TIC_TIMEOUT)
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await asyncio.sleep(20 * TIC_TIMEOUT)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(3 * TIC_TIMEOUT)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await asyncio.sleep(5 * TIC_TIMEOUT)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(3 * TIC_TIMEOUT)


async def fill_orbit_with_garbage(
    canvas, garbage_frames, max_column
):
    while True:
        garbage_delay = get_garbage_delay_tics(year)
        if not garbage_delay:
            await asyncio.sleep(TIC_TIMEOUT)
            continue
        await asyncio.sleep(TIC_TIMEOUT * garbage_delay)
        loop.create_task(fly_garbage(
                canvas,
                column=randint(BORDERS, max_column-1-BORDERS),
                garbage_frame=choice(garbage_frames),
                speed=uniform(MIN_GARBAGE_SPEED, MAX_GARBAGE_SPEED)
            ))


async def print_info(canvas):
    last_phrase_year = None
    while True:
        draw_frame(canvas, 1, 1, f'YEAR: {year}')
        if year in PHRASES.keys():
            draw_frame(canvas, 3, 1, PHRASES[year])
            last_phrase_year = year
        elif last_phrase_year:
            draw_frame(canvas, 3, 1, PHRASES[last_phrase_year], negative=True)

        if DEBUG:
            canvas.border()
        canvas.refresh()
        await asyncio.sleep(TIC_TIMEOUT)


async def canvas_refresh(canvas):
    while True:
        canvas.refresh()
        await asyncio.sleep(TIC_TIMEOUT)


def draw(canvas):
    curses.curs_set(False)
    if BORDERS:
        canvas.border()
    canvas.nodelay(True)
    max_row, max_column = canvas.getmaxyx()

    for _ in range(STARS_NUM):
        loop.create_task(blink(
            canvas,
            randint(BORDERS, max_row-1-BORDERS),
            randint(BORDERS, max_column-1-BORDERS),
            choice(STARS)
        ))

    loop.create_task(
        fill_orbit_with_garbage(
            canvas,
            get_frames(GARBAGE_FRAMES),
            max_column)
    )

    loop.create_task(animate_spaceship(
        canvas,
        max_row // 2,
        max_column // 2,
        get_frames(SPACESHIP_FRAMES)
    ))
    loop.create_task(year_count())

    max_len_phrase = max([len(x) for x in PHRASES.values()])

    loop.create_task(print_info(canvas.derwin(
        5,
        max_len_phrase+2,
        max_row-5,
        max_column-(max_len_phrase+2)
    )))

    if DEBUG:
        loop.create_task(show_obstacles(
            canvas, obstacles
        ))
    loop.create_task(canvas_refresh(canvas))
    loop.run_forever()


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
