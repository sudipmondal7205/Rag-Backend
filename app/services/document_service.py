from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from app.core.pinecone_client import pinecone_index
from langchain_core.documents import Document
from app.core.embeddings import embedding_model
from fastapi import UploadFile
from app.core.llm import llm
import uuid
import fitz



class DocumentService:

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=15
        )
        self.llm = llm


    async def process_pdf(self, file: UploadFile, ):
        
        stream = await file.read()

        docs = []
        with fitz.open(stream=stream, filetype='pdf') as doc:
            for page_no, page in enumerate(doc):

                docs.append(
                    Document(
                        page_content=page.get_text(),
                        metadata={
                            'page_no': page_no
                        }
                    )
                )

        list_docs = await self.split_document(docs)

        title = await self.generate_title(list_docs[0])
        doc_id = str(uuid.uuid4())

        await self.upsert_document(list_docs, doc_id)

        return doc_id, title
    


    async def split_document(self, docs: list[Document]):
        chunks = self.text_splitter.split_documents(docs)
        return chunks



    async def upsert_document(self, documents: list[Document], doc_id: str):

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
                    "page_no": doc.metadata.get("page_no")
                }
            })

        pinecone_index.upsert(vectors)



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