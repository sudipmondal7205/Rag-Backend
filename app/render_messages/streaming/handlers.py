from pprint import pprint
from langchain_core.runnables.schema import StreamEvent
from app.schema.stream_events import Source, SourcesEvent, StatusEvent, TokenEvent, ToolEndEvent, ToolStartEvent


def handle_chat_stream(event):

    chunk = event['data']['chunk']
    if chunk.content:
        return TokenEvent(
            type='token',
            content=chunk.content
        )
    
    return None


def handle_status_event(event):
    chunk = event['data']['chunk']
    return StatusEvent(
        type='status',
        message=chunk.content
    )




def handle_tool_start(event):

    return ToolStartEvent(
        type='tool_start',
        tool=event['name']
    )



def handle_tool_end(event):

    return ToolEndEvent(
        type='tool_end',
        tool=event['name'],
        output=event['data']['output'].artifact
    )


def handle_tool_end_v2(event):
    
    return ToolEndEvent(
        type='tool_end',
        tool=event['name'],
    )



def handle_source_event(event: StreamEvent):
    docs = event.get('data', {}).get('output', {}).get('documents', [])
    sources = [
        Source(
            page=document.metadata.get('source').get('page_no'),
            source=document.metadata.get('source').get('file_name', ''),
            score=document.metadata.get('source').get('score'),
            preview=document.page_content
        )
        for document in docs
    ]
    return SourcesEvent(
        type='sources',
        sources=sources
    )