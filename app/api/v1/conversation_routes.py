from typing import Annotated, List
from app.api.deps import get_agent_service, get_conversation_service, get_current_user
from app.models.user import User
from app.schema.chat_schema import ChatMessage, InputQuery
from app.schema.conversation import ConversationCreate, ConversationResponse
from app.schema.user import TokenUser
from app.services.agent_service import AgentService
from app.services.conversation_service import ConversationService
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import APIRouter
from app.db.session import get_session
from fastapi import Depends
import uuid



router = APIRouter(prefix="/conversation", tags=['conversation'])



@router.get("/get-all-messages")
async def get_all_messages(
        conv_id: uuid.UUID,
        current_user: Annotated[TokenUser, Depends(get_current_user)],
        conversation_service: Annotated[ConversationService, Depends(get_conversation_service)]
    ):
    return await conversation_service.get_messages(thread_id=conv_id, user_id=current_user.id)



@router.get("/get-all", response_model=list[ConversationResponse])
async def get_conversations_by_user(
        current_user: Annotated[TokenUser, Depends(get_current_user)], 
        conversation_service: Annotated[ConversationService, Depends(get_conversation_service)]
    ):
        conversations = await conversation_service.get_conversations_by_user(current_user.id)
        return conversations


@router.post("/create-conversation")
async def create_conversation(
        conversation: ConversationCreate,
        current_user: Annotated[TokenUser, Depends(get_current_user)],
        conversation_service: Annotated[ConversationService, Depends(get_conversation_service)]
    ):
    return await conversation_service.create_conversation(current_user.id, conversation)



@router.put("/chat-with-agent/streaming")
async def chat_with_agent_stream(
        input_query: InputQuery,
        current_user: Annotated[TokenUser, Depends(get_current_user)],
        session: Annotated[AsyncSession, Depends(get_session)],
        agent_service: Annotated[AgentService, Depends(get_agent_service)]
    ):
    return await agent_service.chat_stream(input_query, current_user.id, session)
