from app.schema.stream_events import TokenEvent, ToolEndEvent, ToolStartEvent


def handle_chat_stream(event):

    chunk = event['data']['chunk']

    if chunk.content:
        return TokenEvent(
            type='token',
            content=chunk.content
        )
    return None



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
