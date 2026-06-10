from typing import List
from langchain_core.messages import BaseMessage
from app.schema.chat_schema import ChatAiMessage, ChatMessage, ChatSource, ChatUserMessage



def build_messages(messages: List[BaseMessage]):

    rendered_messages = []
    sources = []

    for message in messages:
        
        msg_type = message.type

        if msg_type == 'human':
            rendered_messages.append(
                ChatUserMessage(
                    role='user',
                    content=message.content
                )
            )
        
        elif msg_type == 'ai':
            if not getattr(message, 'tool_calls', None):
                rendered_messages.append(
                    ChatAiMessage(
                        role='assistant',
                        content=message.content,
                        sources=sources
                    )
                )
                sources = []

        elif msg_type == 'tool':
            sources = []
            artifact = message.artifact
            for artf in artifact:
                source = artf.get('metadata').get('source')
                sources.append(
                    ChatSource(
                        file_name=source.get('file_name', ''),
                        page_no=source.get('page_no', None),
                        score=source.get('score', None),
                        preview=artf.get('page_content')
                    )
                )

            

    return rendered_messages

