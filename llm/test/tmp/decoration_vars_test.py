import asyncio
import uuid_test
from functools import wraps


class Transactional:

    session_registry: dict = {}

    def __init__(self):
        pass

    def __call__(self, function):
        @wraps(function)
        async def decorator(*args, **kwargs):
            key = uuid.uuid4()
            value = uuid.uuid4()
            self.session_registry[key] = value
            print(f"start {key}")
            result = await function(*args, **kwargs)
            del self.session_registry[key]
            print(f"end {key}")
            print(self.session_registry)

        return decorator


@Transactional()
async def test(sleep: bool = False):
    print("run_test")
    if sleep:
        await asyncio.sleep(5)


async def runner():
    await asyncio.gather(
        test(sleep=True),
        test(),
        test(),
        test(),
        test(),
        test(sleep=True),
        test(sleep=True),
        test(),
        test(sleep=True),
        test(),
        test(),
        test(),
        test(sleep=True),
        test()
    )

asyncio.run(
    runner()
)