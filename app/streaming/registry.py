from app.streaming.handlers import handle_chat_stream, handle_tool_end, handle_tool_start



EVENT_HANDLERS = {
    "on_chat_model_stream": handle_chat_stream,
    "on_tool_start": handle_tool_start,
    "on_tool_end": handle_tool_end
}