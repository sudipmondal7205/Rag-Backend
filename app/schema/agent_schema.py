from typing import Annotated, List, Literal, TypedDict
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    doc_id: str
    tool_call_count: int = Field(default=0)


class AgentContext(TypedDict):
    doc_id: str


class AgentStateV2(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_query: str
    updated_query: str
    documents: List[Document]
    loop_count: int
    grade_result: Literal['yes', 'no']


class GradeDocuments(BaseModel):
    binary_score: Literal['yes', 'no'] = Field(
        description="Are the documents relevant to answering the user's base question? 'yes' or 'no'"
    )

class GenerateTitle(BaseModel):
    title: str = Field(
        description="Title of a chat conversation"
    )