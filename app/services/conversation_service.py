import pprint

from app.exceptions.conversation_exception import ConversationNotFoundException
from app.models.conversation import Conversation
from app.render_messages.messages.build_messages import build_messages
from app.repository.conversation_repo import ConversationRepository
from app.schema.chat_schema import ChatMessage
from app.schema.conversation import ConversationCreate, ConversationResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
import uuid



class ConversationService:

    def __init__(
            self, pool: AsyncConnectionPool, 
            session: AsyncSession,  
            conversation_repo: ConversationRepository
        ):
        self._conv_repo = conversation_repo
        self._checkpointer = AsyncPostgresSaver(pool)
        self._session = session

    async def create_conversation(self, user_id: uuid.UUID, conversation_create: ConversationCreate) -> ConversationResponse:
        conversation = Conversation(**conversation_create.model_dump())
        conversation.user_id = user_id
        conv = await self._conv_repo.save_conversation(self._session, conversation)

        if not self._session.in_transaction():
            await self._session.commit()
        else: 
            await self._session.flush()

        conv_response = ConversationResponse.model_validate(conv)
        return conv_response


    async def get_conversation_by_id(self, id: uuid.UUID) -> Conversation:
        return await self._conv_repo.get_conversation(self._session, id)


    async def get_conversations_by_user(self, user_id: uuid.UUID) -> list[ConversationResponse]:
        conversations = await self._conv_repo.get_conversations_by_user(self._session, user_id)
        conv_response = [ConversationResponse.model_validate(conv) for conv in conversations]
        return conv_response


    async def get_messages(self, thread_id: uuid.UUID, user_id: uuid.UUID) -> list[ChatMessage]:

        conversation = await self._conv_repo.get_conversation(self._session, thread_id)
        if conversation is None or (conversation.user_id != user_id):
            raise ConversationNotFoundException(thread_id)
        
        config = {"configurable": {"thread_id": str(thread_id)}}
        checkpoint_tuple = await self._checkpointer.aget(config)

        if checkpoint_tuple is None:
            return []

        messages = checkpoint_tuple.get("channel_values", {}).get("messages", [])
        chat_response = build_messages(messages)

        return chat_response

