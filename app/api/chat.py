from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from app.services.rag_service import rag_service

router = APIRouter(prefix="/api/chat", tags=["RAG Chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None


@router.post("")
def chat_endpoint(payload: ChatRequest):
    """Grounded RAG chat query against 8 sales operations Excel files."""
    user_messages = [m for m in payload.messages if m.role == "user"]
    if not user_messages:
        return {"answer": "Please ask a question regarding sales operations or resort shares.", "sources": []}

    latest_query = user_messages[-1].content
    result = rag_service.query(latest_query)
    return result
