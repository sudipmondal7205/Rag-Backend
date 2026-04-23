from fastapi import FastAPI
from app.db.init_db import init_db
from dotenv import load_dotenv
from app.api.v1.router import api_router


load_dotenv()

app = FastAPI()


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(api_router)