# ==============================================================================
# CampusGPT Backend — Messages API Routes
# ==============================================================================
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.deps import get_current_user_id, get_conversation_service, get_rag_service
from app.schemas.message import MessageCreate, MessageResponse, StreamingToken
from app.services.conversation_service import ConversationService
from app.services.rag_service import RAGService

router = APIRouter(prefix="/conversations/{conversation_id}/messages", tags=["Messages"])


class SendMessageResponse(BaseModel):
    """Response for non-streaming message send."""
    user_message: MessageResponse
    assistant_message: MessageResponse


@router.post("", response_model=SendMessageResponse)
async def send_message(
    conversation_id: UUID,
    data: MessageCreate,
    user_id: UUID = Depends(get_current_user_id),
    conv_service: ConversationService = Depends(get_conversation_service),
    rag_service: RAGService = Depends(get_rag_service),
):
    """Send a message and get AI response (streaming or non-streaming)."""
    # Verify conversation exists and belongs to user
    conversation = await conv_service.get_conversation(conversation_id, user_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    # Save user message
    user_message = await conv_service.add_message(
        conversation_id=conversation_id,
        user_id=user_id,
        role="user",
        content=data.content,
    )

    if data.stream:
        # The request session commits before the stream body runs, so commit explicitly
        await conv_service.session.commit()
        return StreamingResponse(
            stream_response(conversation_id, user_id, user_message, conv_service, rag_service, data.content),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    else:
        # Non-streaming response
        result = await rag_service.answer_question_simple(data.content, user_id)
        assistant_message = await conv_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="assistant",
            content=result["content"],
            sources=result["sources"],
            tokens_used=result["tokens_used"],
        )
        return SendMessageResponse(
            user_message=user_message,
            assistant_message=assistant_message,
        )


async def stream_response(
    conversation_id: UUID,
    user_id: UUID,
    user_message: MessageResponse,
    conv_service: ConversationService,
    rag_service: RAGService,
    content: str,
):
    """Generator for SSE streaming response."""
    import json

    # Send user message confirmation first (already saved by send_message)
    yield f"event: user_message\ndata: {user_message.model_dump_json()}\n\n"

    # Stream AI response
    assistant_content = ""
    sources = []
    tokens_used = 0
    message_id = None

    async for chunk in rag_service.answer_question(content, user_id):
        if chunk["type"] == "token":
            assistant_content += chunk["content"]
            token_data = StreamingToken(token=chunk["content"], done=False)
            yield f"event: token\ndata: {token_data.model_dump_json()}\n\n"
        elif chunk["type"] == "sources":
            sources = chunk["sources"]
            yield f"event: sources\ndata: {json.dumps(sources)}\n\n"
        elif chunk["type"] == "done":
            tokens_used = chunk.get("tokens_used", 0)
            # Save assistant message
            assistant_message = await conv_service.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=assistant_content,
                sources=sources,
                tokens_used=tokens_used,
            )
            await conv_service.session.commit()
            message_id = str(assistant_message.id)
            done_data = StreamingToken(
                token="",
                done=True,
                message_id=assistant_message.id,
                sources=sources,
                tokens_used=tokens_used,
            )
            yield f"event: done\ndata: {done_data.model_dump_json()}\n\n"
        elif chunk["type"] == "error":
            error_data = StreamingToken(token="", done=True, error=chunk["error"])
            yield f"event: error\ndata: {error_data.model_dump_json()}\n\n"
            break


@router.post("/{message_id}/retry", response_model=SendMessageResponse)
async def retry_message(
    conversation_id: UUID,
    message_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    conv_service: ConversationService = Depends(get_conversation_service),
    rag_service: RAGService = Depends(get_rag_service),
):
    """Retry a failed assistant message."""
    # Get the conversation and find the user message before the failed one
    conversation = await conv_service.get_conversation(conversation_id, user_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    # Find the message to retry (should be an assistant message)
    # For simplicity, we'll re-send the last user message
    user_messages = [m for m in conversation.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user message to retry")

    last_user_message = user_messages[-1]

    # Delete the failed assistant message and any after it
    # (Implementation would need message deletion logic)

    # Re-generate
    result = await rag_service.answer_question_simple(last_user_message.content, user_id)
    assistant_message = await conv_service.add_message(
        conversation_id=conversation_id,
        user_id=user_id,
        role="assistant",
        content=result["content"],
        sources=result["sources"],
        tokens_used=result["tokens_used"],
    )

    return SendMessageResponse(
        user_message=MessageResponse.model_validate(last_user_message),
        assistant_message=assistant_message,
    )