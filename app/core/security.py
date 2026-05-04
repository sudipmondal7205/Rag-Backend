from datetime import datetime, timedelta
import re
from typing import Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import jwt
from app.core.config import settings


SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:

    pass


