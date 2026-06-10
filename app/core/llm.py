from langchain.chat_models import BaseChatModel
from langchain_cohere import ChatCohere
from app.core.config import settings



llm = ChatCohere(
    cohere_api_key=settings.COHERE_API_KEY,
    model="command-r7b-12-2024"
)

def get_llm() -> BaseChatModel:
    return llm
