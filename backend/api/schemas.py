"""
AgentMail AI - Pydantic Schemas for API Requests & Responses
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class EmailInputSchema(BaseModel):
    message_id: Optional[str] = Field(None, description="Unique email message ID")
    thread_id: Optional[str] = Field(None, description="Gmail thread ID")
    sender: str = Field(..., description="Sender email address")
    recipient: Optional[str] = Field("pradeep.ai.engineer@example.com", description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Raw or formatted email body")
    timestamp: Optional[str] = Field(None, description="ISO timestamp")


class ApprovalActionSchema(BaseModel):
    message_id: str = Field(..., description="Message ID of the queued draft")
    comment: Optional[str] = Field("", description="Optional supervisor notes")


class EditResponseSchema(BaseModel):
    message_id: str = Field(..., description="Message ID of the queued draft")
    edited_body: str = Field(..., description="User modified email body text")
    comment: Optional[str] = Field("", description="Optional supervisor notes")
