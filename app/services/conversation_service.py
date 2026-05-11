import uuid
from fastapi import UploadFile
from app.exceptions.conversation_exception import ConversationNotFoundException
from app.models.conversation import Conversation
from app.models.user import User
from app.repository.conversation_repo import conversationRepository
from app.schema.chat_schema import ChatResponse
from app.schema.conversation import ConversationCreate, ConversationResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from app.services.document_service import documentService
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.db.conv_checkpoint_pool import pool



class ConversationService:

    def __init__(self):
        self.conv_repo = conversationRepository
        self.doc_service = documentService


    async def create_conversation(self, session: AsyncSession, conversation_create: ConversationCreate) -> ConversationResponse:
        conversation = Conversation(**conversation_create.model_dump())
        conv = await self.conv_repo.create_conversation(session, conversation)

        if not session.in_transaction():
            await session.commit()
        else: 
            await session.flush()

        conv_response = ConversationResponse.model_validate(conv)
        return conv_response


    async def get_conversation_by_id(self, session: AsyncSession, id: uuid.UUID) -> Conversation:
        return await self.conv_repo.get_conversation(session, id)


    async def get_conversations_by_user(self, session: AsyncSession, user_id: uuid.UUID) -> list[ConversationResponse]:
        conversations = await self.conv_repo.get_conversations_by_user(session, user_id)
        conv_response = [ConversationResponse.model_validate(conv) for conv in conversations]
        return conv_response
    

    async def upload_documents(self, session: AsyncSession, user_id: uuid.UUID, file: UploadFile) -> ConversationResponse:
        
        doc_id, title = await self.doc_service.process_pdf(file=file)
        conversation = ConversationCreate(title=title, doc_id=doc_id, user_id=user_id)
        created_conv = await self.create_conversation(session, conversation)

        await session.commit()

        return created_conv


    async def get_messages(self, thread_id: uuid.UUID, user: User, session: AsyncSession) -> list[ChatResponse]:

        conversation = await self.conv_repo.get_conversation(session, thread_id)
        if conversation is None or (conversation.user_id != user.id):
            raise ConversationNotFoundException(thread_id)
        
        checkpointer = AsyncPostgresSaver(pool)
        config = {"configurable": {"thread_id": str(thread_id)}}
        checkpoint_tuple = await checkpointer.aget(config)

        if checkpoint_tuple is None:
            return []
        
        messages = checkpoint_tuple.get("channel_values", {}).get("messages", [])
        chat_response = [ChatResponse.model_validate(msg) for msg in messages]

        return chat_response
        # return messages

        

conversationService = ConversationService()
