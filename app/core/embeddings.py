# from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_cohere import CohereEmbeddings
from langchain_core.documents import Document
from ollama import embeddings
from app.core.config import settings
import os



def get_embedding_model():

    embedding = CohereEmbeddings(
        cohere_api_key=settings.COHERE_API_KEY,
        model="embed-english-v3.0"
    )
    
    return embedding



embedding_model = get_embedding_model()
    