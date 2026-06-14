from typing import Annotated, List, Literal, TypedDict
import uuid
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field



class AgentContext(BaseModel):
    conversation_id: str


class AgentState(TypedDict):
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



class CitedAnswer(BaseModel):
    answer: str = Field(
        description="Provide a comprehensive answer based strictly on the text inside the provided DOC INDEX sections."
    )
    used_document_indexes: List[int] = Field(
        description="The integer values matching the 'DOC INDEX X' headers of the blocks you extracted facts from."
    )