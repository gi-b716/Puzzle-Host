from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel
import os

DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/puzzlehub-auth.db")

os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

SQLITE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"

connect_args = {"check_same_thread": False}
engine = create_async_engine(SQLITE_URL, echo=False, connect_args=connect_args)


async def get_session():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
