from app.schema.stream_events import StatusEvent, TokenEvent, ToolEndEvent, ToolStartEvent


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


def handle_source_event(event):
    pass


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
