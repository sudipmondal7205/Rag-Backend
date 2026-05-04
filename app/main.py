from fastapi import FastAPI
from app.db.init_db import init_db
from dotenv import load_dotenv
from app.api.v1.router import api_router
from contextlib import asynccontextmanager
from app.db.conv_checkpoint_pool import pool


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):

    await pool.open()
    await init_db()
    yield
    await pool.close()


app = FastAPI(lifespan=lifespan)

app.include_router(api_router)