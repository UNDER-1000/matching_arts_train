from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import asyncio
from src.config import Config

DATABASE_URL = os.getenv("DATABASE_URL", Config.db_url)

engine = create_async_engine(DATABASE_URL, echo=True, connect_args={"statement_cache_size": 0}, execution_options={"postgresql_prepare_threshold": None},)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def connect_db():
    while True:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                break
        except Exception as e:
            print(f"DB connection failed: {e}, retrying in 10s...")
            await asyncio.sleep(10)

async def close_db():
    await engine.dispose()

def get_connection():
    return SessionLocal()
