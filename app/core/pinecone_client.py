from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings
import os


def get_pinecone_client():

    api_key = settings.PINECONE_DB_API_KEY

    if not api_key:
        raise ValueError("PINECONE_DB_API_KEY is not set")

    return Pinecone(api_key=api_key)



def get_index() :
    pc = get_pinecone_client()

    if settings.PINECONE_INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=settings.PINECONE_INDEX_NAME,
            dimension=settings.EMBEDDING_DIMENSION,
            metric="cosine",
            spec = ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
    return pc.Index(settings.PINECONE_INDEX_NAME)