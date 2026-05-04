import uuid
from fastapi import UploadFile
from app.models import conversation
from app.models.conversation import Conversation
from app.repository.conversation_repo import conversationRepository
from app.schema.conversation import ConversationCreate, ConversationResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from app.services.document_service import documentService



class ConversationService:

    def __init__(self):
        self.conv_repo = conversationRepository
        self.doc_service = documentService


    async def create_conversation(self, session: AsyncSession, conversation_create: ConversationCreate) -> ConversationResponse:
        conversation = Conversation(**conversation_create.model_dump())
        conv = await self.conv_repo.create_conversation(session, conversation)
        conv_response = ConversationResponse.model_validate(conv)
        return conv_response


    async def get_conversation_by_id(self, session: AsyncSession, id: uuid.UUID) -> Conversation:
        return await self.conv_repo.get_conversation(session, id)


    async def get_conversations_by_user(self, session: AsyncSession, user_id: uuid.UUID) -> list[ConversationResponse]:
        conversations = await self.conv_repo.get_conversations_by_user(session, user_id)
        conv_response = [ConversationResponse.model_validate(conv) for conv in conversations]
        return conv_response
    

    async def upload_documents(self, session: AsyncSession, user_id: uuid.UUID, file: UploadFile):
        
        doc_id, title = await self.doc_service.process_pdf(file=file)
        conversation = ConversationCreate(title=title, doc_id=doc_id, user_id=user_id)
        created_conv = await self.create_conversation(session, conversation)

        return created_conv


conversationService = ConversationService()
