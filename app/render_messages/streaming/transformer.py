from app.render_messages.streaming.handlers import handle_chat_stream, handle_status_event, handle_tool_end, handle_tool_start


def transform_events(event):

    event_type = event['event']

    if event_type == "on_chat_model_stream":

        data = event['data']['chunk']
        if data.tool_calls:
            return handle_status_event(event)
        else:
            return handle_chat_stream(event)

    elif event_type == "on_tool_start":
        return handle_tool_start(event)
    
    elif event_type == "on_tool_end":
        return handle_tool_end(event)
    
    return None