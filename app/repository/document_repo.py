import uuid
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.document import DocumentFile


class DocumentRepository:

    async def get_document(self, session: AsyncSession, document_id: uuid.UUID):
        return await session.get(DocumentFile, document_id)


    async def create_document(self, session: AsyncSession, document: DocumentFile):
        session.add(document)
        await session.flush()
        await session.refresh(document)
        return document
    

    async def get_documents_of_conversation(self, session: AsyncSession, conversation_id: uuid.UUID):
        statement = (
            select(DocumentFile)
            .where(DocumentFile.conversation_id == conversation_id)
            .order_by(DocumentFile.created_at.desc())
        )
        result = await session.exec(statement)
        return result.all()
    

    async def delete_document(self, session: AsyncSession, document: DocumentFile):
        await session.delete(document)