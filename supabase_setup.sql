-- ============================================
-- LTX-2 RunPod Worker - Supabase Storage Setup
-- ============================================
-- This SQL creates the storage bucket and sets up permissions
-- for the LTX-2 video generation worker
--
-- Run this in your Supabase SQL Editor: 
-- https://app.supabase.com/project/YOUR_PROJECT/sql
-- ============================================

-- 1. Create the storage bucket for LTX-2 outputs
-- ============================================
INSERT INTO storage.buckets (id, name, public)
VALUES ('ltx2-outputs', 'ltx2-outputs', false)
ON CONFLICT (id) DO NOTHING;

-- If you want a PUBLIC bucket instead, use:
-- INSERT INTO storage.buckets (id, name, public)
-- VALUES ('ltx2-outputs', 'ltx2-outputs', true)
-- ON CONFLICT (id) DO NOTHING;


-- 2. Storage Policies for PRIVATE bucket (recommended)
-- ============================================
-- These policies allow:
-- - Service role (server-side) to upload/update/delete files
-- - Authenticated users to download via signed URLs
-- - No public access (secure by default)

-- Allow service role to INSERT (upload) files
CREATE POLICY "Service role can upload videos"
ON storage.objects FOR INSERT
TO service_role
WITH CHECK (bucket_id = 'ltx2-outputs');

-- Allow service role to UPDATE files (for upserts)
CREATE POLICY "Service role can update videos"
ON storage.objects FOR UPDATE
TO service_role
USING (bucket_id = 'ltx2-outputs')
WITH CHECK (bucket_id = 'ltx2-outputs');

-- Allow service role to DELETE files
CREATE POLICY "Service role can delete videos"
ON storage.objects FOR DELETE
TO service_role
USING (bucket_id = 'ltx2-outputs');

-- Allow service role to SELECT (needed for signed URL generation)
CREATE POLICY "Service role can read videos"
ON storage.objects FOR SELECT
TO service_role
USING (bucket_id = 'ltx2-outputs');

-- Optional: Allow authenticated users to download via signed URLs
-- (This is usually handled automatically by Supabase signed URL mechanism)
CREATE POLICY "Authenticated users can download videos"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'ltx2-outputs');


-- 3. Alternative: PUBLIC bucket policies
-- ============================================
-- If you set the bucket to public=true above, use these instead:
-- (Uncomment if using public bucket)

-- CREATE POLICY "Anyone can view public videos"
-- ON storage.objects FOR SELECT
-- TO public
-- USING (bucket_id = 'ltx2-outputs');

-- CREATE POLICY "Service role can upload to public bucket"
-- ON storage.objects FOR INSERT
-- TO service_role
-- WITH CHECK (bucket_id = 'ltx2-outputs');

-- CREATE POLICY "Service role can update public bucket"
-- ON storage.objects FOR UPDATE
-- TO service_role
-- USING (bucket_id = 'ltx2-outputs')
-- WITH CHECK (bucket_id = 'ltx2-outputs');

-- CREATE POLICY "Service role can delete from public bucket"
-- ON storage.objects FOR DELETE
-- TO service_role
-- USING (bucket_id = 'ltx2-outputs');


-- 4. Verify bucket setup
-- ============================================
-- Run this to check your bucket was created:
SELECT * FROM storage.buckets WHERE id = 'ltx2-outputs';

-- Run this to check your policies:
SELECT schemaname, tablename, policyname, roles, cmd, qual 
FROM pg_policies 
WHERE tablename = 'objects' 
AND policyname LIKE '%ltx2%';


-- ============================================
-- NOTES
-- ============================================
--
-- PRIVATE BUCKET (recommended):
-- - Set: public = false
-- - Access: Only via signed URLs (time-limited, secure)
-- - Environment: SUPABASE_PUBLIC=false
-- - Best for: Production, user-generated content
--
-- PUBLIC BUCKET:
-- - Set: public = true  
-- - Access: Anyone with URL can download
-- - Environment: SUPABASE_PUBLIC=true
-- - Best for: Demo videos, marketing content
--
-- SIGNED URL TTL:
-- - Default: 86400 seconds (24 hours)
-- - Configure via: SUPABASE_SIGNED_URL_TTL_SECONDS
-- - Can be changed per-request in worker code
--
-- FOLDER STRUCTURE:
-- Worker automatically organizes uploads as:
-- ltx2/{date}/{job_id}/{filename}
-- Example: ltx2/2026-01-13/job_abc123/video.mp4
--
-- ============================================
