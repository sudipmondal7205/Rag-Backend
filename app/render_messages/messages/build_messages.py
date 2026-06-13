import pprint
from typing import List
from langchain_core.messages import BaseMessage
from app.schema.chat_schema import ChatAiMessage, ChatMessage, ChatSource, ChatUserMessage
from app.schema.stream_events import Source



def build_messages(messages: List[BaseMessage]):

    rendered_messages = []

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
                sources = [
                    Source(
                        page=document.get('metadata').get('source').get('page_no'),
                        source=document.get('metadata').get('source').get('file_name', ''),
                        score=document.get('metadata').get('source').get('score'),
                        preview=document.get('page_content')
                    )
                    for document in message.response_metadata.get('sources', [])
                ]
                rendered_messages.append(
                    ChatAiMessage(
                        role='assistant',
                        content=message.content,
                        sources=sources
                    )
                )
                

        # elif msg_type == 'tool':
        #     sources = []
        #     artifact = message.artifact
        #     for artf in artifact:
        #         source = artf.get('metadata').get('source')
        #         sources.append(
        #             ChatSource(
        #                 file_name=source.get('file_name', ''),
        #                 page_no=source.get('page_no', None),
        #                 score=source.get('score', None),
        #                 preview=artf.get('page_content')
        #             )
        #         )

            

    return rendered_messages

