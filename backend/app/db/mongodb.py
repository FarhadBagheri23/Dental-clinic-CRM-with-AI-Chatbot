from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

client = AsyncIOMotorClient(
    settings.mongo_url,
    maxPoolSize=10,
    serverSelectionTimeoutMS=8000,
)


def get_db() -> AsyncIOMotorDatabase:
    return client[settings.mongo_db]


def close_db() -> None:
    client.close()
