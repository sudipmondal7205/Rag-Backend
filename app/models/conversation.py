from typing import List, Optional
from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone
import uuid
from app.models.document import DocumentFile


class Conversation(SQLModel, table = True) :

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    title: str | None

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), index=True), 
        default_factory=lambda: datetime.now(timezone.utc)
    )

    doc_id: str
    
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    user: Optional["User"] = Relationship(back_populates="conversations")
    
    documentfiles: List["DocumentFile"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "order_by": "DocumentFile.created_at"
        }
    )