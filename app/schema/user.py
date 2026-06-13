import uuid
from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    profile_pic: str | None

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(from_attributes=True)


class UserVerifySchema(BaseModel):
    email: EmailStr
    verification_code: str


class TokenUser(BaseModel):
    id: uuid.UUID
    email: EmailStr