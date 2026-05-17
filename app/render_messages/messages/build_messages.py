from typing import List
from langchain_core.messages import BaseMessage
from app.schema.chat_schema import ChatMessage, ChatSource



def build_messages(messages: List[BaseMessage]):

    rendered_messages = []
    sources = []

    for message in messages:
        
        msg_type = message.type

        if msg_type == 'human':
            rendered_messages.append(
                ChatMessage(
                    role='user',
                    content=message.content
                )
            )
        
        elif msg_type == 'ai':
            if not getattr(message, 'tool_calls', None):
                rendered_messages.append(
                    ChatMessage(
                        role='assistant',
                        content=message.content,
                        sources=sources
                    )
                )
                sources = []

        elif msg_type == 'ai':
            artifact = message.artifact
            if artifact['sources']:
                sources = [
                    ChatSource(file_name=src.get('file_name', ''), page_no=src['page_no'], score=src['score']) 
                    for src in artifact['sources']
                ]


    return rendered_messages