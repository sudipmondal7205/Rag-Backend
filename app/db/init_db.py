from sqlmodel import SQLModel
from app.db.session import async_engine
from app.db.conv_checkpoint_pool import pool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.db.base import *


async def init_db():

    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with pool.connection() as conn:
        checkpointer = AsyncPostgresSaver(conn)
        await checkpointer.setup()