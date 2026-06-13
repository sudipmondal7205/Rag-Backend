from datetime import datetime
from pydantic import BaseModel, ConfigDict
import uuid


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str
    created_at: datetime
    conversation_id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)