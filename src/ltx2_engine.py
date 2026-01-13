import os
import time
import torch

from .schema import JobInput
from .config import Settings
from .supabase_uploader import SupabaseUploader
from .utils_images import load_image_from_url, load_image_from_base64
from .utils_media import save_video_mp4


class LTX2Engine:
    """
    LTX-2 video generation engine.
    
    Loads pipelines once at initialization and handles generation requests.
    """
    
    def __init__(self, model_name: str, model_path: str | None, device: str, dtype: str):
        self.model_name = model_name
        self.model_path = model_path
        self.device = device
        self.dtype = torch.float16 if dtype == "float16" else torch.bfloat16
        self.pipe_t2v = None
        self.pipe_i2v = None
        
        self.settings = Settings()
        self.uploader = SupabaseUploader(self.settings)
        
        self._load_pipelines()
    
    def _load_pipelines(self):
        """Load LTX-2 pipelines (called once at worker startup)."""
        t0 = time.time()
        
        # Performance flags
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        
        # Lazy import for container boot resilience
        from diffusers import DiffusionPipeline
        
        # Choose source: cached snapshot path if available, otherwise model name
        source = self.model_path or self.model_name
        
        # ---- Load T2V pipeline ----
        # Try to load dedicated LTX2Pipeline class if available
        try:
            from diffusers import LTX2Pipeline
            print(f"[LTX2] Loading LTX2Pipeline from {source}")
            self.pipe_t2v = LTX2Pipeline.from_pretrained(
                source,
                torch_dtype=self.dtype,
            ).to(self.device)
        except ImportError:
            # Fallback to generic DiffusionPipeline
            print(f"[LTX2] LTX2Pipeline not found, using DiffusionPipeline from {source}")
            self.pipe_t2v = DiffusionPipeline.from_pretrained(
                source,
                torch_dtype=self.dtype,
            ).to(self.device)
        
        # ---- Load I2V pipeline (optional) ----
        # Some builds provide a specific image-to-video pipeline class
        try:
            from diffusers.pipelines.ltx2 import LTX2ImageToVideoPipeline
            print(f"[LTX2] Loading LTX2ImageToVideoPipeline from {source}")
            self.pipe_i2v = LTX2ImageToVideoPipeline.from_pretrained(
                source,
                torch_dtype=self.dtype,
            ).to(self.device)
        except (ImportError, AttributeError):
            print("[LTX2] LTX2ImageToVideoPipeline not available, i2v mode will be limited")
            self.pipe_i2v = None
        
        # Optional speedups (only if supported)
        try:
            self.pipe_t2v.enable_attention_slicing()
            print("[LTX2] Attention slicing enabled")
        except Exception as e:
            print(f"[LTX2] Could not enable attention slicing: {e}")
        
        print(f"[LTX2] Pipelines loaded in {time.time()-t0:.2f}s")
    
    @torch.inference_mode()
    def generate(self, inp: JobInput) -> dict:
        """
        Generate video based on job input.
        
        Args:
            inp: Validated JobInput with generation parameters
        
        Returns:
            Dictionary with supabase upload info and metadata
        """
        # Set up random seed for reproducibility
        generator = None
        if inp.seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(inp.seed)
        
        # Enable low VRAM mode if requested (slower but safer)
        if inp.low_vram:
            try:
                self.pipe_t2v.enable_model_cpu_offload()
                print("[LTX2] Low VRAM mode enabled (CPU offload)")
            except Exception as e:
                print(f"[LTX2] Could not enable CPU offload: {e}")
        
        # Run inference based on mode
        if inp.mode == "i2v":
            if self.pipe_i2v is None:
                raise RuntimeError(
                    "i2v mode requested but LTX2ImageToVideoPipeline is not available. "
                    "This may require a newer diffusers version."
                )
            if not inp.image_url and not inp.image_base64:
                raise ValueError("i2v mode requires either image_url or image_base64")
            
            # Load conditioning image
            image = (
                load_image_from_url(inp.image_url) 
                if inp.image_url 
                else load_image_from_base64(inp.image_base64)
            )
            
            print(f"[LTX2] Running i2v: {inp.prompt[:50]}...")
            out = self.pipe_i2v(
                prompt=inp.prompt,
                negative_prompt=inp.negative_prompt,
                image=image,
                num_inference_steps=inp.steps,
                guidance_scale=inp.guidance,
                generator=generator,
                num_frames=inp.num_frames,
                height=inp.height,
                width=inp.width,
            )
        else:
            # Text-to-video mode
            print(f"[LTX2] Running t2v: {inp.prompt[:50]}...")
            out = self.pipe_t2v(
                prompt=inp.prompt,
                negative_prompt=inp.negative_prompt,
                num_inference_steps=inp.steps,
                guidance_scale=inp.guidance,
                generator=generator,
                num_frames=inp.num_frames,
                height=inp.height,
                width=inp.width,
            )
        
        # Extract frames from pipeline output
        # Diffusers may return different attribute names depending on version
        frames = None
        if hasattr(out, "frames"):
            frames = out.frames
        elif isinstance(out, dict) and "frames" in out:
            frames = out["frames"]
        elif hasattr(out, "videos"):
            frames = out.videos
        elif isinstance(out, dict) and "videos" in out:
            frames = out["videos"]
        else:
            raise RuntimeError(
                f"Could not find frames/videos in pipeline output. "
                f"Output type: {type(out)}, attributes: {dir(out)}"
            )
        
        # Save video to local temporary file
        job_id = os.getenv("RUNPOD_JOB_ID", f"job_{int(time.time())}")
        date_prefix = time.strftime("%Y-%m-%d")
        fname = inp.file_name or "video.mp4"
        local_path = f"/tmp/{fname}"
        
        print(f"[LTX2] Encoding video to {local_path}")
        save_video_mp4(frames=frames, out_path=local_path, fps=inp.fps)
        
        # Upload to Supabase
        remote_path = f"{self.settings.SUPABASE_PREFIX}/{date_prefix}/{job_id}/{fname}"
        print(f"[LTX2] Uploading to Supabase: {remote_path}")
        sb = self.uploader.upload_file(local_path, remote_path)
        
        return {
            "supabase": sb,
            "meta": {
                "seed": inp.seed,
                "fps": inp.fps,
                "num_frames": inp.num_frames,
                "width": inp.width,
                "height": inp.height
            }
        }
