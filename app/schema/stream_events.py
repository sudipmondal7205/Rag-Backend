from typing import Literal, Optional, List, Union, Any
from pydantic import BaseModel
from typing import Any, Optional
import uuid
from pydantic import BaseModel



class InputQuery(BaseModel):
    thread_id: uuid.UUID
    query: str

    


class BaseStreamEvent(BaseModel):

    type: str



class TokenEvent(BaseStreamEvent):

    type: Literal["token"]

    content: str


class StatusEvent(BaseStreamEvent):

    type: Literal["status"]

    message: str



class ToolStartEvent(BaseStreamEvent):

    type: Literal["tool_start"]

    tool: str

    message: Optional[str] = None



class ToolEndEvent(BaseStreamEvent):

    type: Literal["tool_end"]

    tool: str

    output: Optional[Any] = None


class Source(BaseModel):

    page: Optional[int] = None

    source: Optional[str] = None

    score: Optional[float] = None

    preview: Optional[str] = None


class SourcesEvent(BaseStreamEvent):

    type: Literal["sources"]

    sources: List[Source]


class ErrorEvent(BaseStreamEvent):

    type: Literal["error"]

    message: str


class DoneEvent(BaseStreamEvent):

    type: Literal["done"]


StreamEvent = Union[
    TokenEvent,
    StatusEvent,
    ToolStartEvent,
    ToolEndEvent,
    SourcesEvent,
    ErrorEvent,
    DoneEvent
]