"""_summary_ command to generate model schema
    just convenient for development
    synchronous command to get any exception from awaitable Tortoise's functions
"""

from tortoise import Tortoise, run_async
import settings


async def main():
    await Tortoise.init(config=settings.TORTOISE_ORM)
    await Tortoise.generate_schemas()


if __name__ == "__main__":
    run_async(main())
