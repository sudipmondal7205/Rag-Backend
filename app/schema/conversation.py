from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    title: str = None
    doc_id: str
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: str
    doc_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)