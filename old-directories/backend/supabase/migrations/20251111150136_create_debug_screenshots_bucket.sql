-- Create bucket for debug screenshots and HTML files
-- This bucket stores error screenshots and HTML dumps from production debugging

-- Create the bucket
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'debug-screenshots',
    'debug-screenshots',
    false, -- Private bucket, requires signed URLs
    10485760, -- 10MB limit per file
    ARRAY['image/png', 'text/html']
)
ON CONFLICT (id) DO UPDATE
SET
    public = false,
    file_size_limit = 10485760,
    allowed_mime_types = ARRAY['image/png', 'text/html'];

-- Create policy for authenticated backend service
-- Only service role can upload/read (for backend debugging)
CREATE POLICY "Service role can manage debug screenshots"
ON storage.objects
FOR ALL
TO service_role
USING (bucket_id = 'debug-screenshots')
WITH CHECK (bucket_id = 'debug-screenshots');

-- Optional: Policy for authenticated users to read their company's debug screenshots
-- (if you want to expose them via admin panel in the future)
CREATE POLICY "Authenticated users can read debug screenshots"
ON storage.objects
FOR SELECT
TO authenticated
USING (bucket_id = 'debug-screenshots');
