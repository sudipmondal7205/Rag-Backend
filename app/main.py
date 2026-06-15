from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from fastapi.exceptions import RequestValidationError
from app.api.v1.router import api_router
from app.core.lifespan import lifespan
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.exceptions.handlers import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler
)



load_dotenv()


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


app.include_router(api_router)