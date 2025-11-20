-- Create f29-pdfs storage bucket
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'f29-pdfs',
  'f29-pdfs',
  false,
  52428800, -- 50MB limit
  ARRAY['application/pdf']
)
ON CONFLICT (id) DO NOTHING;

-- Create RLS policies for f29-pdfs bucket
-- Allow authenticated users to upload PDFs to their company's folder
CREATE POLICY "Users can upload F29 PDFs to their company folder"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'f29-pdfs' AND
  (storage.foldername(name))[1] IN (
    SELECT c.id::text 
    FROM companies c
    JOIN sessions s ON s.company_id = c.id
    WHERE s.user_id = auth.uid()
  )
);

-- Allow authenticated users to read F29 PDFs from their company's folder
CREATE POLICY "Users can read F29 PDFs from their company folder"
ON storage.objects FOR SELECT
TO authenticated
USING (
  bucket_id = 'f29-pdfs' AND
  (storage.foldername(name))[1] IN (
    SELECT c.id::text 
    FROM companies c
    JOIN sessions s ON s.company_id = c.id
    WHERE s.user_id = auth.uid()
  )
);

-- Allow service role full access (for backend operations)
CREATE POLICY "Service role has full access to f29-pdfs"
ON storage.objects FOR ALL
TO service_role
USING (bucket_id = 'f29-pdfs')
WITH CHECK (bucket_id = 'f29-pdfs');