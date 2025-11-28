"""
Chat Router - HTTP endpoints for custom chat interface.

Provides REST API for chat without ChatKit dependency.
Designed for use with Expo/React Native frontends.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.services.chat import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


# ============================================================================
# Request/Response Models
# ============================================================================


class RequiredContext(BaseModel):
    """Context to load before executing the agent."""

    identifier: str = Field(
        ..., description="UI component identifier (e.g., 'document_detail', 'tax_summary_iva')"
    )
    entity_id: str | None = Field(
        None, description="Entity UUID or ID (e.g., document UUID, '2025-11')"
    )
    entity_type: str | None = Field(
        None, description="Entity type (e.g., 'sales_document', 'tax_period', 'contact')"
    )


class ChatRequest(BaseModel):
    """Request model for chat endpoints."""

    message: str = Field(..., description="User message")
    thread_id: str | None = Field(
        None, description="Thread ID (auto-generated if not provided)"
    )
    company_id: str | None = Field(None, description="Company ID for context")
    required_context: RequiredContext | None = Field(
        None, description="Required context to load before agent execution"
    )
    metadata: dict | None = Field(None, description="Additional metadata")


class ChatResponse(BaseModel):
    """Response model for non-streaming chat endpoint."""

    response: str = Field(..., description="Assistant response")
    thread_id: str = Field(..., description="Thread ID")
    metadata: dict = Field(default_factory=dict, description="Response metadata")


class UploadResponse(BaseModel):
    """Response model for file upload endpoint."""

    success: bool = Field(..., description="Upload success status")
    attachment_id: str = Field(..., description="Unique attachment identifier")
    filename: str = Field(..., description="Original filename")
    mime_type: str = Field(..., description="File MIME type")
    size: int = Field(..., description="File size in bytes")


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/chat/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
) -> UploadResponse:
    """
    Upload file endpoint for chat attachments.

    Accepts a file upload and returns an attachment_id that can be referenced
    in subsequent chat requests.

    **Example (JavaScript/React Native):**
    ```javascript
    const formData = new FormData();
    formData.append('file', {
      uri: fileUri,
      type: 'image/jpeg',
      name: 'photo.jpg'
    });

    const response = await fetch('/api/chat/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });

    const data = await response.json();
    console.log('Attachment ID:', data.attachment_id);

    // Use attachment_id in chat request
    await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        message: "Analiza esta imagen",
        metadata: {
          attachments: [data.attachment_id]
        }
      })
    });
    ```

    Args:
        file: File upload (multipart/form-data)
        user: Authenticated user data (from JWT token)

    Returns:
        UploadResponse with attachment_id and file metadata
    """
    # Extract user_id from JWT token
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token"
        )

    try:
        # Read file content
        file_content = await file.read()

        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {max_size / 1024 / 1024}MB"
            )

        # Generate attachment ID
        from app.agents.core.memory_attachment_store import (
            generate_attachment_id,
            store_attachment_content,
        )

        attachment_id = generate_attachment_id("chat")

        # Store file content in memory
        store_attachment_content(attachment_id, file_content)

        logger.info(
            f"📎 File uploaded | "
            f"user={user_id[:8]} | "
            f"attachment_id={attachment_id} | "
            f"filename={file.filename} | "
            f"size={len(file_content)} bytes | "
            f"mime_type={file.content_type}"
        )

        return UploadResponse(
            success=True,
            attachment_id=attachment_id,
            filename=file.filename or "unknown",
            mime_type=file.content_type or "application/octet-stream",
            size=len(file_content),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ File upload error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}",
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: dict = Depends(get_current_user),
) -> ChatResponse:
    """
    Chat endpoint (blocking).

    Returns complete agent response after execution finishes.

    **Example 1: Simple text message**
    ```javascript
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        message: "¿Cuál es mi RUT?",
        thread_id: "thread_123",
        company_id: "company_456"
      })
    });

    const data = await response.json();
    console.log(data.response);
    ```

    **Example 2: Message with image attachment**
    ```javascript
    // First, upload the file
    const formData = new FormData();
    formData.append('file', {
      uri: imageUri,
      type: 'image/jpeg',
      name: 'receipt.jpg'
    });

    const uploadRes = await fetch('/api/chat/upload', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });
    const { attachment_id } = await uploadRes.json();

    // Then send message with attachment reference
    const chatRes = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        message: "¿Qué información puedes extraer de este documento?",
        thread_id: "thread_123",
        company_id: "company_456",
        metadata: {
          attachments: [attachment_id]
        }
      })
    });
    ```

    Args:
        request: ChatRequest with message and optional thread_id/company_id
        user: Authenticated user data (from JWT token)

    Returns:
        ChatResponse with full assistant response
    """
    # Extract user_id from JWT token
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token"
        )

    # Generate thread_id if not provided
    thread_id = request.thread_id or f"thread_{uuid.uuid4().hex[:16]}"

    # Extract required_context from metadata if present there
    required_context = request.required_context
    if not required_context and request.metadata:
        # Check if required_context is nested in metadata
        context_data = request.metadata.get("required_context")
        if context_data:
            try:
                required_context = RequiredContext(**context_data)
                logger.debug("📦 Extracted required_context from metadata")
            except Exception as e:
                logger.warning(f"⚠️  Failed to parse required_context from metadata: {e}")

    # Log request parameters
    context_info = "none"
    if required_context:
        context_info = f"{required_context.identifier}"
        if required_context.entity_id:
            context_info += f" (entity_id={required_context.entity_id[:8]}...)"
        if required_context.entity_type:
            context_info += f" [type={required_context.entity_type}]"

    logger.info(
        f"🚀 POST /api/chat | "
        f"user={user_id[:8]} | "
        f"thread={thread_id[:16]} | "
        f"company={request.company_id[:8] if request.company_id else 'none'} | "
        f"context={context_info} | "
        f"message_len={len(request.message)} chars"
    )

    try:
        # Initialize service
        service = ChatService()

        # Execute chat
        result = await service.execute(
            message=request.message,
            thread_id=thread_id,
            user_id=user_id,
            company_id=request.company_id,
            required_context=required_context,
            metadata=request.metadata,
        )

        # Log successful completion
        logger.info(
            f"✅ POST /api/chat | "
            f"thread={thread_id[:16]} | "
            f"status=200 OK | "
            f"response_len={len(result['response'])} chars"
        )

        return ChatResponse(**result)

    except Exception as e:
        logger.error(f"❌ Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando chat: {str(e)}",
        )
