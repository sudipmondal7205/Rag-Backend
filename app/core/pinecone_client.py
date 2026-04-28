from pinecone import Pinecone, ServerlessSpec
import os


def get_pinecone_client():
    api_key = os.getenv("PINECONE_DB_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_DB_API_KEY is not set")

    return Pinecone(api_key=api_key)


def get_index() :
    pc = get_pinecone_client()

    INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
    EMBEDDING_DIMENSION = os.getenv("EMBEDDING_DIMENSION")

    if INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=INDEX_NAME,
            dimension=int(EMBEDDING_DIMENSION),
            metric="cosine",
            spec = ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
    return pc.Index(INDEX_NAME)