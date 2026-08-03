import asyncio
from app.database.postgres import init_tiger_schema

async def main():
    await init_tiger_schema()
    print("Migration completed successfully.")

if __name__ == "__main__":
    asyncio.run(main())