from langchain.embeddings import Embeddings
from langchain_cohere import CohereEmbeddings
from app.core.config import settings



embedding_model = CohereEmbeddings(
    cohere_api_key=settings.COHERE_API_KEY,
    model="embed-english-v3.0"
)


def get_embedding_model() -> Embeddings:
    return embedding_model
    