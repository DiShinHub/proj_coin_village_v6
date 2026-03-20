import asyncio


async def async_test():
    print("asdf")

loop = asyncio.get_event_loop()
loop = loop.run_until_complete(async_test())
