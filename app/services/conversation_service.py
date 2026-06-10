from app.exceptions.conversation_exception import ConversationNotFoundException
from app.models.conversation import Conversation
from app.models.user import User
from app.render_messages.messages.build_messages import build_messages
from app.repository.conversation_repo import ConversationRepository
from app.schema.chat_schema import ChatMessage
from app.schema.conversation import ConversationCreate, ConversationResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
import uuid



class ConversationService:

    def __init__(self, pool: AsyncConnectionPool, conversation_repo: ConversationRepository):
        self._conv_repo = conversation_repo
        self._checkpointer = AsyncPostgresSaver(pool)

    async def create_conversation(self, session: AsyncSession, conversation_create: ConversationCreate) -> ConversationResponse:
        conversation = Conversation(**conversation_create.model_dump())
        conv = await self._conv_repo.create_conversation(session, conversation)

        if not session.in_transaction():
            await session.commit()
        else: 
            await session.flush()

        conv_response = ConversationResponse.model_validate(conv)
        return conv_response


    async def get_conversation_by_id(self, session: AsyncSession, id: uuid.UUID) -> Conversation:
        return await self._conv_repo.get_conversation(session, id)


    async def get_conversations_by_user(self, session: AsyncSession, user_id: uuid.UUID) -> list[ConversationResponse]:
        conversations = await self._conv_repo.get_conversations_by_user(session, user_id)
        conv_response = [ConversationResponse.model_validate(conv) for conv in conversations]
        return conv_response


    async def get_messages(self, thread_id: uuid.UUID, user_id: uuid.UUID, session: AsyncSession) -> list[ChatMessage]:

        conversation = await self._conv_repo.get_conversation(session, thread_id)
        print(conversation)
        print(user_id)
        if conversation is None or (conversation.user_id != user_id):
            raise ConversationNotFoundException(thread_id)
        
        config = {"configurable": {"thread_id": str(thread_id)}}
        checkpoint_tuple = await self._checkpointer.aget(config)

        if checkpoint_tuple is None:
            return []
        
        messages = checkpoint_tuple.get("channel_values", {}).get("messages", [])
        chat_response = build_messages(messages)

        return chat_response

