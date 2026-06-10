from pprint import pprint

from openai import evals

from app.render_messages.streaming.handlers import handle_chat_stream, handle_source_event, handle_status_event, handle_tool_end, handle_tool_end_v2, handle_tool_start


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


def transform_events_v2(event):

    kind = event['event']
    metadata = event.get('metadata', {})
    node_name = metadata.get('langgraph_node', '')
    chunk = event.get('data', {}).get('chunk')

    if kind == 'on_tool_start':
        return handle_tool_start(event)
        
    elif kind == 'on_tool_end':
        return handle_tool_end_v2(event)        
    
    elif kind == 'on_chat_model_stream':
        if node_name == 'agent' or node_name == 'generator':
            if chunk and hasattr(chunk, 'content') and chunk.content:
                return handle_chat_stream(event)
        
    elif kind == 'on_chain_end' and node_name =='generator':
        return handle_source_event(event)
