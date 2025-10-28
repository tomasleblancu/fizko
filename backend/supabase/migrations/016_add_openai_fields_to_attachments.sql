-- Add OpenAI Files API integration fields to attachments table
-- These fields store references to OpenAI file_id and vector_store_id for PDFs
-- that are uploaded to OpenAI for file_search functionality

-- Add openai_file_id column (stores OpenAI file ID like "file-abc123")
ALTER TABLE attachments
ADD COLUMN IF NOT EXISTS openai_file_id TEXT;

-- Add openai_vector_store_id column (stores OpenAI vector store ID like "vs-abc123")
ALTER TABLE attachments
ADD COLUMN IF NOT EXISTS openai_vector_store_id TEXT;

-- Add comments for documentation
COMMENT ON COLUMN attachments.openai_file_id IS 'OpenAI Files API file ID (for PDFs uploaded for file_search)';
COMMENT ON COLUMN attachments.openai_vector_store_id IS 'OpenAI Vector Store ID containing this file (for file_search)';

-- Create index for querying by vector_store_id (useful for cleanup/management)
CREATE INDEX IF NOT EXISTS idx_attachments_openai_vector_store_id
ON attachments(openai_vector_store_id)
WHERE openai_vector_store_id IS NOT NULL;

-- Create index for querying by file_id (useful for cleanup/management)
CREATE INDEX IF NOT EXISTS idx_attachments_openai_file_id
ON attachments(openai_file_id)
WHERE openai_file_id IS NOT NULL;
