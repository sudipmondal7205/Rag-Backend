import re
import uuid
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.conversation import Conversation


class ConversationRepository:

    async def get_conversation(self, session: AsyncSession, conv_id: uuid.UUID) -> Conversation:
        return await session.get(Conversation, conv_id)


    async def create_conversation(self, session: AsyncSession, conversation: Conversation) -> Conversation:
        
        async with session.begin():
            session.add(conversation)

        await session.refresh(conversation)
        return conversation


    async def get_conversations_by_user(self, session: AsyncSession, user_id: uuid.UUID):
        statement = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
        )
        result = await session.exec(statement)
        return result.all()
    




conversationRepository = ConversationRepository()