import asyncio
from io import BytesIO
from fastapi.responses import StreamingResponse
from langchain.chat_models import BaseChatModel
from langchain.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.db.session import async_session_factory
from app.exceptions.conversation_exception import ConversationNotFoundException
from app.exceptions.document_exception import DocumentNotFoundException
from app.exceptions.file_exception import FileException
from app.exceptions.security_exception import UnauthorizedUserException
from app.models.conversation import Conversation
from app.models.document import DocumentFile
from app.repository.conversation_repo import ConversationRepository
from sqlmodel.ext.asyncio.session import AsyncSession
from app.repository.document_repo import DocumentRepository
from app.schema.agent_schema import GenerateTitle
from app.schema.document import DocumentResponse
from app.schema.stream_events import DocUploadEvent, ErrorEvent
from langchain_core.prompts import ChatPromptTemplate
from app.core.pinecone_client import pinecone_index
from langchain_core.documents import Document
from fastapi import UploadFile
from supabase import AsyncClient
import uuid
import fitz




class DocumentService:

    def __init__(self, 
        llm: BaseChatModel, 
        embedding: Embeddings, 
        session: AsyncSession, 
        conversation_repo: ConversationRepository,
        document_repo: DocumentRepository,
        supabase_client: AsyncClient
    ):
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=15
        )
        self._llm = llm
        self._embedding_model = embedding
        self._session = session
        self._conversation_repo = conversation_repo
        self._document_repo = document_repo
        self._supabase_client = supabase_client


    async def upload_document(self, file: UploadFile, user_id: uuid.UUID, conversation_id: uuid.UUID | None):
        if conversation_id:
            conversation = await self._conversation_repo.get_conversation(self._session, conversation_id)
            if conversation is None or conversation.user_id != user_id:
                raise ConversationNotFoundException(conversation_id)
        else:
            conversation = Conversation(user_id=user_id)
            conversation = await self._conversation_repo.save_conversation(self._session, conversation)

        document_file = DocumentFile(
            filename=file.filename,
            content_type=file.content_type,
            conversation_id=conversation.id
        )

        supabase_file_path = f"users/{user_id}/conversation/{conversation.id}/{document_file.id}/{file.filename}"
        document_file.file_path = supabase_file_path

        async def progress_generator():
            created_document = None
            uploaded_storage_path = None
            completed = False
            cancelled = False
            async_results = []

            try:
                file_bytes = await file.read()
                yield f"data: {DocUploadEvent(percentage=0, status="Uploading file...").model_dump_json()}\n\n"
                await self._supabase_client.storage.from_("documents").upload(
                    path=supabase_file_path,
                    file=file_bytes,
                    file_options={"content-type": file.content_type, "upsert": "true"}
                )
                uploaded_storage_path = supabase_file_path

                created_document = await self._document_repo.create_document(self._session, document_file)
                await self._session.commit()

                yield  f"data: {DocUploadEvent(percentage=40, status="File upload complete...").model_dump_json()}\n\n"

                async for event in self.process_pdf(
                    file.filename, 
                    file_bytes, 
                    created_document,
                    conversation,
                    async_results
                ):
                    yield event
        
                await self._session.commit()
                completed = True

                yield f"data: {DocUploadEvent(
                    percentage=100,
                    status='Done',
                    document=DocumentResponse.model_validate(created_document)
                ).model_dump_json()}\n\n"

            except asyncio.CancelledError:
                cancelled = True
                asyncio.create_task(self._cleanup_canceled_task(
                        uploaded_storage_path, 
                        created_document.id if created_document else None,
                        async_results
                    )
                )
                raise

            except Exception as e:
                yield f"data: {ErrorEvent(type='error', message=str(e)).model_dump_json()}\n\n"
                
            finally:
                if cancelled:
                    return
                if not completed:
                    if created_document is not None:
                        await self._delete_document_vectors(created_document)
                        await self._document_repo.delete_document(self._session, created_document)
                        await self._session.commit()
                    else:
                        await self._session.rollback()

                    if uploaded_storage_path is not None:
                        await self._supabase_client.storage.from_('documents').remove([uploaded_storage_path])


        return StreamingResponse(progress_generator(), media_type="text/event-stream")


    async def process_pdf(self, filename: str,
            file_bytes: bytes, 
            document_file: DocumentFile, 
            conversation: Conversation,
            async_results: list
        ):
        batch_size = 30
        docs = self._get_file_docs(file_bytes, filename)
        list_docs = self._split_document(docs)

        if len(list_docs) == 0:
            yield f"data: {ErrorEvent(type='error', message="Could not process file.").model_dump_json()}\n\n"
            return

        if conversation.title is None or len(conversation.title) == 0:
            conversation.title = await self._generate_title(list_docs[0])
            
        batches = self._chunker(list_docs, batch_size)

        for i, chunk in enumerate(batches, start=1):
            result = await self._upsert_document(chunk, str(document_file.id), str(conversation.id))
            async_results.append(result)

            completed = min((batch_size * i), len(list_docs))
            percentage = (completed / len(list_docs)) * 50 + 40

            yield f"data: {DocUploadEvent(percentage=int(percentage), status='Processing...').model_dump_json()}\n\n"
        
        for result in async_results:
            result.get()
        await self._conversation_repo.save_conversation(self._session, conversation)


        

    def _split_document(self, docs: list[Document]):
        chunks = self._text_splitter.split_documents(docs)
        return chunks


    def _get_file_docs(self, file_bytes: bytes, filename: str) -> list[Document]:
        docs = []
        with fitz.open(stream=file_bytes, filetype='pdf') as doc:
            for page_no, page in enumerate(doc, start=1):
                docs.append(
                    Document(
                        page_content=page.get_text(),
                        metadata={
                            'file_name': filename,
                            'page_no': page_no
                        }
                    )
                )
        return docs


    async def _upsert_document(self, documents: list[Document], document_id: str, conversation_id: str):
        texts = [doc.page_content for doc in documents]
        embeddings = await self._embedding_model.aembed_documents(texts)
        vectors = []
        for doc, emb in zip(documents, embeddings):
            vectors.append({
                "id": str(uuid.uuid4()),
                "values": emb,
                "metadata": {
                    "document_id": document_id,
                    "conversation_id": conversation_id,
                    "text": doc.page_content,
                    "file_name": doc.metadata.get("file_name"),
                    "page_no": doc.metadata.get("page_no")
                }
            })
        response = pinecone_index.upsert(vectors, async_req=True)
        return response



    def _chunker(self, documents: list[Document], batch_size: int):
        return [documents[pos : pos + batch_size] for pos in range(0, len(documents), batch_size)]



    async def _generate_title(self, document: Document) -> str:
        prompt = ChatPromptTemplate.from_template(
            """
            You are a metadata assistant. Based on the following document
            generate a 3-5 word title for this document content. Just write the title, nothing else.
            Document Context: {context}
            Title:
            """
        )
        title_generator = self._llm.with_structured_output(GenerateTitle)
        chain = (prompt | title_generator)
        result = await chain.ainvoke({'context': document.page_content})
        return result.title.strip(" #*$")
    


    async def get_documents_of_conversation(self, user_id: uuid.UUID, conversation_id: uuid.UUID) -> list[DocumentResponse]:
        conversation = await self._conversation_repo.get_conversation(self._session, conversation_id)
        if conversation is None or (conversation.user_id != user_id):
            raise ConversationNotFoundException(conversation_id)
        
        documents = await self._document_repo.get_documents_of_conversation(self._session, conversation_id)
        return [DocumentResponse.model_validate(doc) for doc in documents]
    
    

    async def get_document_stream(self, user_id: uuid.UUID, document_id: uuid.UUID):
        document = await self._document_repo.get_document(self._session, document_id)
        if document is None:
            raise DocumentNotFoundException(document_id)
        
        conversation = await self._conversation_repo.get_conversation(self._session, document.conversation_id)
        if conversation is None or (conversation.user_id != user_id):
            raise UnauthorizedUserException(detail="Unauthorized access to this asset.")
        
        try:
            file_bytes = await self._supabase_client.storage.from_("documents").download(document.file_path)
        except Exception as e:
            raise FileException(detail=f"Failed to fetch file from cloud : {str(e)}")
        
        return StreamingResponse(
            content=BytesIO(file_bytes),
            media_type=document.content_type,
            headers={"Content-Disposition": f"inline; filename={document.filename}"}
        )
    
    
    async def _delete_document_vectors(self, document: DocumentFile):
        pinecone_index.delete(
            filter={
                "document_id": str(document.id)
            }
        )

    async def _delete_conversation_vectors(self, conversation: Conversation):
        pinecone_index.delete(
            filter={
                "conversation_id": str(conversation.id)
            }
        )


    async def _delete_storage_files(self, document_files: list[DocumentFile]):
        file_paths = [document.file_path for document in document_files if document.file_path]
        try:
            if file_paths:
                await self._supabase_client.storage.from_('documents').remove(file_paths)
        except Exception as e:
            raise FileException(detail=f"Could not remove file from cloud: {str(e)}")


    async def delete_document(self, user_id: uuid.UUID, document_id: uuid.UUID):
        document = await self._document_repo.get_document(self._session, document_id)
        if document is None:
            raise DocumentNotFoundException(document_id)

        conversation = await self._conversation_repo.get_conversation(self._session, document.conversation_id)
        if conversation is None or (conversation.user_id != user_id):
            raise UnauthorizedUserException(detail="Unauthorized access to this asset.")
        
        await self._delete_document_vectors(document)
        await self._delete_storage_files([document])
        await self._document_repo.delete_document(self._session, document)
        await self._session.commit()



    async def delete_documents_for_conversation(self, conversation: Conversation):
        document_files = await self._document_repo.get_documents_of_conversation(self._session, conversation.id)
        await self._delete_conversation_vectors(conversation)
        await self._delete_storage_files(list(document_files))



    async def _cleanup_canceled_task(self, 
            uploaded_storage_path: str | None, 
            document_id: uuid.UUID | None, 
            async_results: list
        ):
        async with async_session_factory() as session:
            for result in async_results:
                try:
                    result.get()
                except Exception:
                    pass

            if document_id is not None:
                document = await self._document_repo.get_document(session, document_id)
                if document is not None:
                    await self._delete_document_vectors(document)
                    await self._document_repo.delete_document(session, document)
                await session.commit()

        if uploaded_storage_path is not None:
            await self._supabase_client.storage.from_('documents').remove([uploaded_storage_path])
        
        