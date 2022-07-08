from asyncio import sleep
from itertools import cycle


def cycle_with_repeat(iterable, repeat=1):
    """
    generator that returns items from itertools.cycle repeatedly
    e.g. [a,b,c], repeat=2 -> a,a,b,b,c,c,a,a,b,...
    """
    for item in cycle(iterable):
        for _ in range(repeat):
            yield item


def validate_value(value, value_min, value_max):
    if value < value_min:
        return value_min
    if value > value_max:
        return value_max
    return value


async def asleep(tics=1):
    for _ in range(tics):
        await sleep(0)


def get_garbage_delay_tics(year):
    if year < 1961:
        return None
    elif year < 1969:
        return 20
    elif year < 1981:
        return 14
    elif year < 1995:
        return 10
    elif year < 2010:
        return 8
    elif year < 2020:
        return 6
    else:
        return 2
