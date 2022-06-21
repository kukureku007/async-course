import asyncio
import random


COROUTINES_NUM = 4


async def count_to(position, count):
    for i in range(1, count+1):
        print(f'coroutine {position}:  {i}, max: {count}')
        await asyncio.sleep(0)


if __name__ == '__main__':
    coroutines = []
    for i in range(COROUTINES_NUM):
        coroutines.append(count_to(i, random.randint(1, 6)))

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        if len(coroutines) == 0:
            break
