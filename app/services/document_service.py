from io import BytesIO

from fastapi.responses import StreamingResponse
from langchain.chat_models import BaseChatModel
from langchain.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.exceptions.conversation_exception import ConversationNotFoundException
from app.exceptions.document_exception import DocumentNotFoundException
from app.exceptions.file_exception import FileException
from app.exceptions.security_exception import UnauthorizedUserException
from app.models.conversation import Conversation
from app.models.document import DocumentFile
from app.models.user import User
from app.repository.conversation_repo import ConversationRepository
from sqlmodel.ext.asyncio.session import AsyncSession
from app.repository.document_repo import DocumentRepository
from app.schema.agent_schema import GenerateTitle
from app.schema.conversation import ConversationResponse
from app.schema.stream_events import DocUploadEvent
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
            doc_id = str(uuid.uuid4())
            conversation = Conversation(doc_id=doc_id, user_id=user_id)
            conversation = await self._conversation_repo.create_conversation(self._session, conversation)


        document_file = DocumentFile(
            filename=file.filename,
            content_type=file.content_type,
            conversation_id=conversation.id
        )
        supabase_file_path = f"users/{user_id}/conversation/{conversation.id}/{document_file.id}/{file.filename}"
        document_file.file_path = supabase_file_path

        file_bytes = await file.read()
        try:
            await self._supabase_client.storage.from_("documents").upload(
                path=supabase_file_path,
                file=file_bytes,
                file_options={"content-type": file.content_type, "upsert": "true"}
            )
        except Exception as e:
            raise FileException(f"Could not upload file: {str(e)}")

        created_document = await self._document_repo.create_document(self._session, document_file)


        return await self.process_pdf(file.filename, file_bytes, conversation)


    async def process_pdf(self, filename: str, file_bytes: bytes, conversation: Conversation):
        batch_size = 30

        docs = self._get_file_docs(file_bytes, filename)
        list_docs = self._split_document(docs)
        
        if len(list_docs) == 0:
            raise FileException(detail=f"Could not process {filename}")
        
        if conversation.title is None or len(conversation.title) == 0:
            conversation.title = await self._generate_title(list_docs[0])
            
        batches = self._chunker(list_docs, batch_size)

        async def progress_generator():
            for i, chunk in enumerate(batches, start=1):

                await self._upsert_document(chunk, conversation.doc_id)

                completed = min((batch_size * i), len(list_docs))
                percentage = (completed / len(list_docs)) * 100

                yield f"data: {DocUploadEvent(percentage=int(percentage), status='Uploading...').model_dump_json()}\n\n"
            
            updated_conversation = await self._conversation_repo.update_conversation(self._session, conversation)
            await self._session.commit()

            yield f"data: {DocUploadEvent(
                percentage=100,
                status='Done',
                conversation=ConversationResponse.model_validate(updated_conversation)
            ).model_dump_json()}\n\n"

        return StreamingResponse(progress_generator(), media_type="text/event-stream")

        

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


    async def _upsert_document(self, documents: list[Document], doc_id: str):
        texts = [doc.page_content for doc in documents]
        embeddings = await self._embedding_model.aembed_documents(texts)
        vectors = []
        
        for doc, emb in zip(documents, embeddings):
            vectors.append({
                "id": str(uuid.uuid4()),
                "values": emb,
                "metadata": {
                    "doc_id": doc_id,
                    "text": doc.page_content,
                    "file_name": doc.metadata.get("file_name"),
                    "page_no": doc.metadata.get("page_no")
                }
            })

        pinecone_index.upsert(vectors, async_req=True)



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
    


    async def get_documents_of_conversation(self, user_id: uuid.UUID, conversation_id: uuid.UUID):
        conversation = await self._conversation_repo.get_conversation(self._session, conversation_id)
        if conversation is None or (conversation.user_id != user_id):
            raise ConversationNotFoundException(conversation_id)
        
        return await self._document_repo.get_documents_of_conversation(self._session, conversation_id)
    
    

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
