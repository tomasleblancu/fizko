"""
Attachment processor for ChatKit.

Converts ChatKit attachments to OpenAI Agents framework format.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from chatkit.types import UserMessageItem

logger = logging.getLogger(__name__)


async def convert_attachments_to_content(
    item: UserMessageItem,
    attachment_store
) -> List[Dict[str, Any]]:
    """
    Convert UserMessageItem content (text + attachments) to OpenAI Agents framework format.

    Returns a list of content items that can include:
    - {"type": "input_text", "text": "..."}
    - {"type": "input_image", "image_url": "data:image/png;base64,..."}

    Args:
        item: ChatKit UserMessageItem
        attachment_store: Attachment store for retrieving attachment data

    Returns:
        List of content parts in OpenAI Agents format
    """
    from app.agents.core import get_attachment_content
    from app.services.storage.attachment_storage import get_attachment_storage

    content_parts = []

    # First, process text content
    for part in item.content:
        text = getattr(part, "text", None)
        if text:
            content_parts.append({
                "type": "input_text",
                "text": text
            })

    # Then, check if item has attachments
    attachment_ids = []
    attachment_objects = []

    # Method 1: Check for attachments attribute directly on item
    if hasattr(item, 'attachments') and item.attachments:
        logger.info(f"📦 Found attachments attribute: {item.attachments}")
        attachments_list = item.attachments if isinstance(item.attachments, list) else [item.attachments]

        for att in attachments_list:
            # If it's already an Attachment object, extract the ID
            if hasattr(att, 'id'):
                attachment_ids.append(att.id)
                attachment_objects.append(att)
            # If it's just a string ID
            elif isinstance(att, str):
                attachment_ids.append(att)

    # Method 2: Check for attachment references in content parts
    for part in item.content:
        attachment_ref = getattr(part, "attachment", None)
        if attachment_ref:
            attachment_id = getattr(attachment_ref, "id", None) or getattr(attachment_ref, "attachment_id", None)
            if attachment_id and attachment_id not in attachment_ids:
                attachment_ids.append(attachment_id)
                if hasattr(attachment_ref, 'mime_type'):
                    attachment_objects.append(attachment_ref)

    # Process all found attachments
    if attachment_ids:
        logger.info(f"🔗 Processing {len(attachment_ids)} attachment(s): {attachment_ids}")
        storage = get_attachment_storage()

        for i, attachment_id in enumerate(attachment_ids):
            logger.info(f"🔗 Processing attachment {i+1}/{len(attachment_ids)}: {attachment_id}")

            # Try to get full attachment object first (has all metadata)
            attachment_obj = attachment_objects[i] if i < len(attachment_objects) else None

            if attachment_obj:
                # We have the full Attachment object from ChatKit
                mime_type = getattr(attachment_obj, 'mime_type', '')
                filename = getattr(attachment_obj, 'name', 'unknown')

                logger.info(f"📎 Using attachment object: {mime_type}, {filename}")
            else:
                # Fallback: Get metadata from store
                metadata = attachment_store.get_attachment_metadata(attachment_id)
                if metadata:
                    mime_type = metadata.get("mime_type", "")
                    filename = metadata.get("name", "")
                    logger.info(f"📎 Using attachment metadata: {mime_type}, {filename}")
                else:
                    logger.warning(f"⚠️ No metadata found for {attachment_id}, skipping")
                    continue

            # For images, ALWAYS use base64
            if mime_type.startswith("image/"):
                base64_content = get_attachment_content(attachment_id)

                # Fallback: Try to load from Supabase Storage if not in memory
                if not base64_content:
                    logger.warning(f"⚠️ Image content not found in memory for {attachment_id}, trying Supabase...")
                    try:
                        import base64 as b64
                        file_data = storage.download_attachment(attachment_id)
                        if file_data:
                            base64_content = b64.b64encode(file_data).decode('utf-8')
                            logger.info(f"✅ Loaded image from Supabase Storage: {len(base64_content)} chars")
                    except Exception as e:
                        logger.error(f"❌ Failed to load from Supabase: {e}")

                if base64_content:
                    # IMPORTANT: Clean the base64 string (remove any whitespace/newlines)
                    base64_content = base64_content.strip().replace('\n', '').replace('\r', '').replace(' ', '')

                    # Validate that it's proper base64
                    try:
                        import base64 as b64
                        decoded = b64.b64decode(base64_content)
                        logger.info(f"✅ Base64 validation passed: {len(decoded)} bytes, magic: {decoded[:2].hex() if len(decoded) >= 2 else 'N/A'}")
                    except Exception as e:
                        logger.error(f"❌ Invalid base64 content for {attachment_id}: {e}")
                        content_parts.append({
                            "type": "input_text",
                            "text": f"[Imagen con formato inválido: {filename}]"
                        })
                        continue

                    # Create data URL - agents framework expects this format
                    data_url = f"data:{mime_type};base64,{base64_content}"
                    content_parts.append({
                        "type": "input_image",
                        "image_url": data_url
                    })
                    logger.info(f"📸 Added image to content: {filename} (base64, {len(base64_content)} chars)")
                else:
                    logger.warning(f"⚠️ Image content not available from any source for {attachment_id}")
                    # If base64 not available, skip the image
                    content_parts.append({
                        "type": "input_text",
                        "text": f"[Imagen no disponible: {filename}]"
                    })
            else:
                # For non-image files (PDFs, etc.)
                # Check if this PDF has been uploaded to OpenAI (has vector_store_id)
                openai_metadata = await attachment_store.get_openai_metadata(attachment_id)

                if openai_metadata and 'vector_store_id' in openai_metadata:
                    # PDF is available via FileSearchTool - inform the agent
                    content_parts.append({
                        "type": "input_text",
                        "text": f"El usuario ha adjuntado el documento PDF '{filename}'. Usa la herramienta file_search para leer y analizar su contenido."
                    })
                    logger.info(f"📄 PDF with vector_store available: {filename}")
                else:
                    # PDF not in OpenAI - just add reference
                    content_parts.append({
                        "type": "input_text",
                        "text": f"[Archivo adjunto: {filename}]"
                    })
                    logger.info(f"📄 Added file reference: {filename}")

    return content_parts
