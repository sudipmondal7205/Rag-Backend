from langchain_cohere import ChatCohere
from app.core.config import settings
import os


def get_llm():

    llm = ChatCohere(
        cohere_api_key=settings.COHERE_API_KEY,
        model="command-r7b-12-2024"
    )

    return llm


llm =  get_llm()