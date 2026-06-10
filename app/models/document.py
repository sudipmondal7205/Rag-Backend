from typing import Optional
import uuid
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, DateTime
from datetime import datetime, timezone

class DocumentFile(SQLModel, table = True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)

    filename: str
    content_type: str
    file_path: Optional[str]

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), index=True),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    conversation_id: uuid.UUID = Field(foreign_key="conversation.id", ondelete='CASCADE')
    conversation: Optional["Conversation"] = Relationship(back_populates='documentfiles')