import uuid
from pydantic import BaseModel


class InputQuery(BaseModel):
    thread_id: uuid.UUID
    query: str


class ChatResponse(BaseModel):
    role: str
    type: str
    content: str