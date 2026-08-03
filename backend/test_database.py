import asyncio
from app.database.postgres import engine, AsyncSessionLocal, init_tiger_schema
from app.database.models import ReviewModel, FindingModel
# pyrefly: ignore [missing-import]
from sqlalchemy import text

async def test_connection():
    # Test basic connection
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")

    # Test creating a review
    async with AsyncSessionLocal() as session:
        review = ReviewModel(
            id="test_review_1",
            repository="org/test",
            pr_number=1,
            status="pending"
        )
        session.add(review)
        await session.commit()
        print("✅ Test review inserted")

        # Clean up
        await session.delete(review)
        await session.commit()
        print("✅ Test review deleted")

    print("\n✅ Database module is working!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_connection())