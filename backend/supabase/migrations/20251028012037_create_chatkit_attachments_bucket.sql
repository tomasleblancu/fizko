-- Create bucket for ChatKit attachments if it doesn't exist
INSERT INTO storage.buckets (id, name, public)
VALUES ('chatkit-attachments', 'chatkit-attachments', false)
ON CONFLICT (id) DO NOTHING;

-- Allow authenticated users to upload their own attachments
-- This policy allows uploads during the chat session
CREATE POLICY "Users can upload chatkit attachments"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'chatkit-attachments');

-- Allow authenticated users to read attachments
-- OpenAI needs to be able to download these files via signed URLs
CREATE POLICY "Users can read chatkit attachments"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'chatkit-attachments');

-- Allow service role to manage all attachments (for cleanup, etc)
CREATE POLICY "Service role can manage chatkit attachments"
ON storage.objects FOR ALL
TO service_role
USING (bucket_id = 'chatkit-attachments');
