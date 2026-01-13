import os
from supabase import create_client, Client
from .config import Settings


class SupabaseUploader:
    """Handles uploading generated videos to Supabase Storage."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
    
    def upload_file(self, local_path: str, remote_path: str) -> dict:
        """
        Upload a local file to Supabase Storage.
        
        Args:
            local_path: Path to local file
            remote_path: Desired path in Supabase bucket
        
        Returns:
            Dictionary with bucket, path, signed_url, and public_url
        """
        bucket = self.settings.SUPABASE_BUCKET
        
        with open(local_path, "rb") as f:
            data = f.read()
        
        # Upload with upsert to overwrite if exists
        res = self.client.storage.from_(bucket).upload(
            path=remote_path,
            file=data,
            file_options={"content-type": "video/mp4", "upsert": "true"},
        )
        
        out = {
            "bucket": bucket,
            "path": remote_path,
            "signed_url": None,
            "public_url": None
        }
        
        # Generate appropriate URL based on bucket visibility
        if self.settings.SUPABASE_PUBLIC:
            out["public_url"] = self.client.storage.from_(bucket).get_public_url(remote_path)
        else:
            if self.settings.SUPABASE_SIGNED_URL_TTL_SECONDS > 0:
                signed = self.client.storage.from_(bucket).create_signed_url(
                    remote_path,
                    self.settings.SUPABASE_SIGNED_URL_TTL_SECONDS
                )
                # Handle different response formats from supabase-py versions
                out["signed_url"] = (
                    signed.get("signedURL") or 
                    signed.get("signed_url") or 
                    signed.get("url")
                )
        
        return out
