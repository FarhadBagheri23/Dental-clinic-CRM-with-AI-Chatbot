from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .config import settings

client = AsyncIOMotorClient(
    settings.mongo_url,
    maxPoolSize=10,
    serverSelectionTimeoutMS=8000,
)


def get_db() -> AsyncIOMotorDatabase:
    return client[settings.mongo_db]
