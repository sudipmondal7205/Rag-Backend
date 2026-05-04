from functools import cache

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from app.core.pinecone_client import get_index
from langchain_core.documents import Document
from app.core.embeddings import get_embedding
from fastapi import UploadFile
from app.core.llm import llm
import uuid
import fitz



class DocumentService:

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        self.llm = llm



    async def process_pdf(self, file: UploadFile):
        
        stream = await file.read()

        docs = []
        with fitz.open(stream=stream, filetype='pdf') as doc:
            for page_num, page in enumerate(doc):

                docs.append(
                    Document(page_content=page.get_text())
                )

        list_docs = await self.split_document(docs)
        texts = [doc.page_content for doc in list_docs]

        title = await self.generate_title(list_docs[0])
        doc_id = str(uuid.uuid4())

        await self.upsert_document(texts, doc_id)

        return doc_id, title
    


    async def split_document(self, docs):

        chunks = self.text_splitter.split_documents(docs)

        return chunks



    async def upsert_document(self, texts: list[str], doc_id: str):

        embeddings = get_embedding(texts)
        index = get_index()

        vectors = []
        for i, (text, emb) in enumerate(zip(texts, embeddings)):
            vectors.append({
                "id": str(uuid.uuid4()),
                "values": emb,
                "metadata": {
                    "doc_id": doc_id,
                    "text": text
                }
            })

        index.upsert(vectors)


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
        return result.content.strip()
    
        


    


documentService = DocumentService()