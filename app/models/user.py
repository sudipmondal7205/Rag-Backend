from sqlmodel import SQLModel, Field, Relationship
from app.models.conversation import Conversation
from typing import List
import uuid


class User(SQLModel, table = True) :

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)

    name: str = Field(unique=True, index=True)
    password: str
    email: str = Field(unique=True, index=True)

    conversations: List["Conversation"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "order_by": "Conversation.created_at"
        }
    )