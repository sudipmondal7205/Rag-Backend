import uuid
from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    name: str
    password: str
    email: EmailStr


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)