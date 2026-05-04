from http import HTTPStatus
import uuid
from click import File
from app.schema.chat_schema import ChatResponse, InputQuery
from app.schema.conversation import ConversationCreate, ConversationResponse
from app.services.agent_service import chatService
from fastapi import APIRouter, HTTPException, UploadFile
from app.services.conversation_service import conversationService
from app.db.session import get_session
from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession


router = APIRouter()


@router.post("/chat")
async def chat_with_agent(input_query: InputQuery, session: AsyncSession = Depends(get_session)):
    try:
        
        return await chatService.ask_question(session, input_query)

    except Exception as e:
        HTTPException(status_code=500, detail=str(e))


@router.get("/get-all-messages", response_model=list[ChatResponse])
async def get_all_messages(conv_id: uuid.UUID):

    return await chatService.get_messages(thread_id=conv_id)


@router.post("/upload-docs", response_model=ConversationResponse)
async def upload_document(user_id: str, file: UploadFile = File(...), session: AsyncSession = Depends(get_session)):
    
    if not file.filename.endswith('.pdf'):
        return HTTPException(status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE, detail="Only .pdf files are allowed!!!")
    
    conversation = await conversationService.upload_documents(session=session, user_id=user_id, file=file)

    return conversation


@router.get("/conversation/all", response_model=list[ConversationResponse])
async def get_conversations_by_user(user_id: uuid.UUID, session = Depends(get_session)):

    conversations = await conversationService.get_conversations_by_user(session, user_id)
    return conversations


@router.post("/create-conversation")
async def create_conversation(conversation: ConversationCreate, session: AsyncSession = Depends(get_session)):
    return await conversationService.create_conversation(session, conversation)