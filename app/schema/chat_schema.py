from importlib import metadata
from typing import Any, Dict, Optional
import uuid
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, model_validator



class InputQuery(BaseModel):
    thread_id: uuid.UUID
    query: str



class ChatResponse(BaseModel):
    id: str
    type: str
    action: Optional[str] = None
    content: Optional[dict] = None
    
    @model_validator(mode='before')
    @classmethod
    def preprocess(cls, data: BaseMessage) -> Dict[str, Any]:

        msg_type = data.type
        msg_additional_kwargs = data.additional_kwargs
        action = None
        content = None
        if msg_type == 'ai':
            if msg_additional_kwargs.get('finish_reason') == 'TOOL_CALL':
                action = f"tool-call: {msg_additional_kwargs['tool_calls'][0]['function']['name']}"
                content = {"tool_plan": msg_additional_kwargs['tool_plan']}
            else:
                action = "responded"
                content = {"message": data.content}
        elif msg_type == 'human':
            action = "user-input"
            content = {"message": data.content}
        
        else:
            action = "reteieved-docs"
            content = {
                "tool-name": data.name,
                "artifact": data.artifact
            }

        return {
            'id': data.id,
            'type': data.type,
            'action': action,
            'content': content
        }
    

