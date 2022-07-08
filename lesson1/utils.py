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
