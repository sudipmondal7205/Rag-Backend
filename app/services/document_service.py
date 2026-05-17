import asyncio
from fastapi.responses import StreamingResponse
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.exceptions.file_exception import FileException
from app.models.conversation import Conversation
from app.models.user import User
from app.repository.conversation_repo import ConversationRepository
from sqlmodel.ext.asyncio.session import AsyncSession
from app.schema.conversation import ConversationResponse
from app.schema.stream_events import DocUploadEvent
from langchain_core.prompts import ChatPromptTemplate
from app.core.pinecone_client import pinecone_index
from langchain_core.documents import Document
from app.core.embeddings import embedding_model
from fastapi import UploadFile
from app.core.llm import llm
import uuid
import fitz




class DocumentService:

    def __init__(self, session: AsyncSession, conversation_repo: ConversationRepository):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=15
        )
        self.llm = llm
        self.session = session
        self.conversation_repo = conversation_repo


    async def process_pdf(self, file: UploadFile, user: User):
        batch_size = 30

        docs = await self._read_file(file)
        list_docs = await self._split_document(docs)
        
        if len(list_docs) == 0:
            raise FileException(detail=f"Could not process {file.filename}")
        
        title = await self.generate_title(list_docs[0])
        doc_id = str(uuid.uuid4())
        batches = self._chunker(list_docs, batch_size)

        async def progress_generator():
            for i, chunk in enumerate(batches, start=1):

                await self._upsert_document(chunk, doc_id)

                completed = min((batch_size * i), len(list_docs))
                percentage = (completed / len(list_docs)) * 100

                yield f"data: {DocUploadEvent(percentage=int(percentage), status='Uploading...').model_dump_json()}\n\n"
            
            conversation = Conversation(title=title, doc_id= doc_id, user_id=user.id)
            conversation = await self.conversation_repo.create_conversation(self.session, conversation)
            await self.session.commit()

            yield f"data: {DocUploadEvent(
                percentage=100,
                status='Done',
                conversation=ConversationResponse.model_validate(conversation)
            ).model_dump_json()}\n\n"

        return StreamingResponse(progress_generator(), media_type="text/event-stream")

        

    async def _split_document(self, docs: list[Document]):
        chunks = self.text_splitter.split_documents(docs)
        return chunks


    async def _read_file(self, file: UploadFile) -> list[Document]:
        stream = await file.read()
        docs = []
        with fitz.open(stream=stream, filetype='pdf') as doc:
            for page_no, page in enumerate(doc, start=1):
                docs.append(
                    Document(
                        page_content=page.get_text(),
                        metadata={
                            'file_name': file.filename,
                            'page_no': page_no
                        }
                    )
                )
        return docs


    async def _upsert_document(self, documents: list[Document], doc_id: str):
        texts = [doc.page_content for doc in documents]
        embeddings = await embedding_model.aembed_documents(texts)
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



    async def generate_title(self, document: Document) -> str:
        prompt = ChatPromptTemplate.from_template(
            """
            You are a metadata assistant. Based on the following document.
            generate a 3-5 word title for this document content.
            Document Context: {context}
            Title:
            """
        )
        chain = prompt | self.llm
        result = await chain.ainvoke({'context': document.page_content})
        return result.content.strip(" #*$")
    
