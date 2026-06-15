from sqlmodel import SQLModel, Field, Relationship
from app.enums.user_enum import UserRole
from app.models.conversation import Conversation
from typing import List, Literal
import uuid
from pydantic import EmailStr

class User(SQLModel, table = True) :

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)

    email: EmailStr = Field(unique=True, index=True)
    password: str
    role: UserRole = Field(default=UserRole.USER)
    full_name: str = Field(min_length=2, max_length=50)

    profile_pic: str | None = Field(default=None)

    conversations: List["Conversation"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "order_by": "Conversation.created_at"
        }
    )