# from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_cohere import CohereEmbeddings
from langchain_core.documents import Document
from app.core.config import settings
import os



def get_embedding(doc: list[str]):

    embedding = CohereEmbeddings(
        cohere_api_key=settings.COHERE_API_KEY,
        model="embed-english-v3.0"
    )
    
    response = embedding.embed_documents(doc)

    return response