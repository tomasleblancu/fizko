-- Make chatkit-attachments bucket public for read access
-- This allows the frontend to display uploaded images directly in ChatKit

-- Update bucket to be public
UPDATE storage.buckets
SET public = true
WHERE id = 'chatkit-attachments';

-- Drop the old authenticated-only read policy
DROP POLICY IF EXISTS "Users can read chatkit attachments" ON storage.objects;

-- Create new policy that allows public read access
CREATE POLICY "Public read access for chatkit attachments"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'chatkit-attachments');

-- Keep the authenticated upload policy
-- (The existing "Users can upload chatkit attachments" policy remains unchanged)

-- Keep the service role management policy
-- (The existing "Service role can manage chatkit attachments" policy remains unchanged)
