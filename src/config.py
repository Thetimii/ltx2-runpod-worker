import os
from pydantic import BaseModel


class Settings(BaseModel):
    """Configuration for LTX-2 RunPod worker."""
    
    # Model settings
    MODEL_NAME: str = os.getenv("MODEL_NAME", "Lightricks/LTX-2")
    DEVICE: str = os.getenv("DEVICE", "cuda")
    # "float16" is default for speed; add "bfloat16" if your GPU supports it well
    DTYPE: str = os.getenv("DTYPE", "float16")
    
    # Supabase settings
    SUPABASE_URL: str = os.environ["SUPABASE_URL"]
    SUPABASE_SERVICE_ROLE_KEY: str = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    SUPABASE_BUCKET: str = os.getenv("SUPABASE_BUCKET", "ltx2-outputs")
    SUPABASE_PREFIX: str = os.getenv("SUPABASE_PREFIX", "ltx2")
    SUPABASE_PUBLIC: bool = os.getenv("SUPABASE_PUBLIC", "false").lower() == "true"
    SUPABASE_SIGNED_URL_TTL_SECONDS: int = int(os.getenv("SUPABASE_SIGNED_URL_TTL_SECONDS", "86400"))
