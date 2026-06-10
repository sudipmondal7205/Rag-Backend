from fastapi import FastAPI
from dotenv import load_dotenv
from app.api.v1.router import api_router
from app.core.lifespan import lifespan



load_dotenv()


app = FastAPI(lifespan=lifespan)

app.include_router(api_router)