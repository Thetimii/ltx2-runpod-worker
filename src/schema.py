from typing import Literal, Optional
from pydantic import BaseModel, Field


Mode = Literal["t2v", "i2v"]


class JobInput(BaseModel):
    """Input schema for LTX-2 video generation job."""
    
    mode: Mode = "t2v"
    prompt: str
    negative_prompt: Optional[str] = None
    
    # Generation parameters
    seed: Optional[int] = None
    steps: int = 30
    guidance: float = 7.0
    
    # Video parameters
    fps: int = 24
    num_frames: int = 49
    height: int = 512
    width: int = 512
    
    # Image conditioning (for i2v mode)
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    
    # Output settings
    output_format: Literal["mp4"] = "mp4"
    file_name: Optional[str] = None
    return_signed_url: bool = True
    
    # Performance toggles
    low_vram: bool = False


class SupabaseResult(BaseModel):
    """Result of Supabase upload."""
    
    bucket: str
    path: str
    signed_url: Optional[str] = None
    public_url: Optional[str] = None


class JobOutput(BaseModel):
    """Output schema for completed job."""
    
    ok: bool
    mode: Mode
    supabase: SupabaseResult
    meta: dict = Field(default_factory=dict)
