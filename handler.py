import os
import time
import runpod

from src.config import Settings
from src.ltx2_engine import LTX2Engine
from src.schema import JobInput, JobOutput

settings = Settings()

# ---- RunPod cached model locator ----
CACHE_DIR = "/runpod-volume/huggingface-cache/hub"


def find_cached_model_path(model_name: str) -> str | None:
    """
    Find the cached model snapshot path in RunPod's volume.
    
    RunPod Cached Models are stored at:
    /runpod-volume/huggingface-cache/hub/models--{org}--{name}/snapshots/{hash}/
    
    Args:
        model_name: HuggingFace model name (e.g., "Lightricks/LTX-2")
    
    Returns:
        Path to snapshot directory, or None if not found
    """
    cache_name = model_name.replace("/", "--")
    snapshots_dir = os.path.join(CACHE_DIR, f"models--{cache_name}", "snapshots")
    
    if os.path.exists(snapshots_dir):
        snaps = sorted(os.listdir(snapshots_dir))
        if snaps:
            snapshot_path = os.path.join(snapshots_dir, snaps[-1])
            print(f"[RunPod] Found cached model at: {snapshot_path}")
            return snapshot_path
    
    print(f"[RunPod] Cached model not found, will download from HuggingFace")
    return None


MODEL_NAME = settings.MODEL_NAME
MODEL_PATH = find_cached_model_path(MODEL_NAME)

# ---- Global engine (loaded once per worker) ----
print(f"[RunPod] Initializing LTX2Engine with model: {MODEL_NAME}")
engine = LTX2Engine(
    model_name=MODEL_NAME,
    model_path=MODEL_PATH,
    device=settings.DEVICE,
    dtype=settings.DTYPE,
)
print("[RunPod] Worker ready to accept jobs")


def handler(job):
    """
    RunPod serverless handler function.
    
    Args:
        job: RunPod job dict with 'id' and 'input' fields
    
    Returns:
        JobOutput dict or error dict
    """
    t0 = time.time()
    job_id = job.get("id", "unknown")
    raw = job.get("input", {})
    
    print(f"[RunPod] Processing job {job_id}")
    
    # Validate input with Pydantic
    try:
        inp = JobInput.model_validate(raw)
    except Exception as e:
        print(f"[RunPod] Invalid input for job {job_id}: {e}")
        return {"ok": False, "error": f"Invalid input: {str(e)}"}
    
    # Generate video
    try:
        result = engine.generate(inp)
        out = JobOutput(
            ok=True,
            mode=inp.mode,
            supabase=result["supabase"],
            meta={
                **result.get("meta", {}),
                "inference_seconds": round(time.time() - t0, 3)
            },
        )
        print(f"[RunPod] Job {job_id} completed in {time.time() - t0:.2f}s")
        return out.model_dump()
    except Exception as e:
        print(f"[RunPod] Job {job_id} failed: {e}")
        return {"ok": False, "error": str(e)}


# Start RunPod serverless worker
runpod.serverless.start({"handler": handler})
