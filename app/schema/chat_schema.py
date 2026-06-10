from typing import Literal, Optional, List, Union, Any
from pydantic import BaseModel
from typing import Any, Dict, Optional
import uuid




class InputQuery(BaseModel):
    thread_id: uuid.UUID
    query: str

   

class ChatSource(BaseModel):
    file_name: str = ""
    page_no: int | None = None
    score: float | None = None
    preview: str = ""

class ChatMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str


class ChatUserMessage(ChatMessage):
    role: Literal['user']


class ChatAiMessage(ChatMessage):
    role: Literal['assistant']
    sources: List[ChatSource] = []