from pydantic import BaseModel, Field, ConfigDict 
from datetime import datetime
from typing import Optional, List
import re

E164_REGEX = r"^\+\d{1,15}$"

class WebhookPayload(BaseModel):
    message_id: str = Field(..., min_length=1)
    sender: str = Field(..., alias="from", pattern=E164_REGEX)
    recipient: str = Field(..., alias="to", pattern=E164_REGEX)
    ts: datetime = Field(...)
    text: Optional[str] = Field(None, max_length=4096)

    model_config = ConfigDict(populate_by_name=True)

class MessageRow(BaseModel):
    message_id: str
    from_msisdn: str
    to_msisdn: str
    ts: datetime
    text: Optional[str]
    created_at: datetime

class PaginatedResponse(BaseModel):
    data: List[MessageRow]
    total: int
    limit: int
    offset: int