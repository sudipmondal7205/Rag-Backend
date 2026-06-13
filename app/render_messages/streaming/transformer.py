import pprint

from langchain.messages import AIMessage

from app.render_messages.streaming.handlers import handle_chat_stream, handle_source_event, handle_status_event, handle_tool_end, handle_tool_end_v2, handle_tool_start
from langchain_core.runnables.schema import StreamEvent

from app.schema.stream_events import TokenEvent



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


def transform_events_v2(event: StreamEvent):

    kind = event['event']
    metadata = event.get('metadata', {})
    node_name = metadata.get('langgraph_node', '')
    chunk = event.get('data', {}).get('chunk')
    name = event.get('name')

    if kind == 'on_tool_start':
        return handle_tool_start(event)
        
    elif kind == 'on_tool_end':
        return handle_tool_end_v2(event)        
    
    elif kind == 'on_chat_model_stream':
        if node_name == 'agent' or node_name == 'generator':
            if chunk and hasattr(chunk, 'content') and chunk.content:
                return handle_chat_stream(event)
        
    elif kind == 'on_chain_end' and name =='generator':
        output = event.get('data', {}).get('output', {})
        if isinstance(output.get('messages')[0], AIMessage) and output.get('messages')[0].response_metadata.get('answer_given') == "false":
            return TokenEvent(type='token', content=output.get('messages', {})[0].content)
        return handle_source_event(event)
