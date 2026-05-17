from typing import List

from app.api.deps import get_current_user, get_doc_service
from app.exceptions.file_exception import FileException
from app.models.user import User
from app.schema.chat_schema import ChatMessage, InputQuery
from app.schema.conversation import ConversationCreate, ConversationResponse
from app.services.conversation_service import ConversationService, conversationService
from sqlmodel.ext.asyncio.session import AsyncSession
from app.services.agent_service import chatService
from fastapi import APIRouter, HTTPException, UploadFile
from app.db.session import get_session
from fastapi import Depends
from http import HTTPStatus
from click import File
import uuid

from app.services.document_service import DocumentService


router = APIRouter(prefix="/conversation")


@router.post("/chat-with-agent", response_model=ChatMessage)
async def chat_with_agent(
    input_query: InputQuery,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    return await chatService.ask_question(session, input_query, current_user)



@router.get("/get-all-messages", response_model=List[ChatMessage])
async def get_all_messages(
        conv_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
    ):
    return await conversationService.get_messages(thread_id=conv_id, user=current_user, session=session)


@router.post("/upload-docs")
async def upload_document(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user),
        document_service: DocumentService = Depends(get_doc_service)
    ):
    if not file.filename.endswith('.pdf'):
        raise FileException(detail="Only .pdf files are allowed!!!")
    
    return await document_service.process_pdf(file, current_user)
    


@router.get("/get-all", response_model=list[ConversationResponse])
async def get_conversations_by_user(
        user: User = Depends(get_current_user), 
        session = Depends(get_session)
    ):
        conversations = await conversationService.get_conversations_by_user(session, user.id)
        return conversations


@router.post("/create-conversation")
async def create_conversation(
        conversation: ConversationCreate, 
        session: AsyncSession = Depends(get_session)
    ):
    return await conversationService.create_conversation(session, conversation)


@router.post("/chat-with-agent/streaming")
async def chat_with_agent_stream(
        input_query: InputQuery,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)
    ):
    return await chatService.ask_question_stream(session, input_query, current_user)
    