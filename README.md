# LTX-2 RunPod Serverless Worker

Production-ready RunPod Serverless worker for **Lightricks/LTX-2** video generation with:

- ⚡ **Fast cold starts** using RunPod Cached Models
- 🎥 **Text-to-video** and **image-to-video** generation
- ☁️ **Supabase Storage** integration with signed URLs
- 🔧 **Low VRAM mode** for smaller GPUs
- 🐳 **Docker-based** deployment

## Features

- **Minimal cold-start overhead**: Uses RunPod's cached model system to avoid downloading 10GB+ models on every worker spin-up
- **One-time pipeline load**: Pipelines loaded globally per worker, not per request
- **Multiple generation modes**: Text-to-video (t2v) and image-to-video (i2v) with extensible architecture
- **Automatic Supabase uploads**: Videos uploaded with organized date-based paths
- **Flexible output**: Public URLs or signed URLs with configurable TTL
- **VRAM management**: Optional CPU offload for memory-constrained GPUs

## Architecture

```
┌─────────────┐
│ RunPod Job  │
│   Input     │
└──────┬──────┘
       │
       v
┌──────────────────┐
│  handler.py      │  ← RunPod entrypoint
│  - Validates     │
│  - Routes to     │
│    engine        │
└──────┬───────────┘
       │
       v
┌──────────────────┐
│ LTX2Engine       │  ← Loaded once per worker
│  - T2V pipeline  │
│  - I2V pipeline  │
│  - Generation    │
└──────┬───────────┘
       │
       v
┌──────────────────┐
│ Supabase Upload  │
│  - MP4 encoding  │
│  - Storage API   │
│  - URL signing   │
└──────┬───────────┘
       │
       v
┌─────────────┐
│   Result    │
│   JSON      │
└─────────────┘
```

## Quick Start

### 1. Environment Variables (RunPod Secrets)

Set these in your RunPod Serverless endpoint configuration:

#### HuggingFace / Model Caching
```bash
HF_HOME=/runpod-volume/huggingface-cache
TRANSFORMERS_CACHE=/runpod-volume/huggingface-cache
HF_HUB_CACHE=/runpod-volume/huggingface-cache/hub
# HF_TOKEN=hf_...  # Only if using gated models
```

#### Supabase (required)
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...  # Server-side key, keep secret!
SUPABASE_BUCKET=ltx2-outputs
SUPABASE_PREFIX=ltx2
SUPABASE_PUBLIC=false  # Set to "true" for public bucket
SUPABASE_SIGNED_URL_TTL_SECONDS=86400  # 1 day
```

#### Optional Model Settings
```bash
MODEL_NAME=Lightricks/LTX-2
DEVICE=cuda
DTYPE=float16  # or "bfloat16" if your GPU supports it well
```

### 2. Build and Push Docker Image

```bash
# Build
docker build -t your-dockerhub-username/ltx2-runpod-worker:latest .

# Push to Docker Hub
docker push your-dockerhub-username/ltx2-runpod-worker:latest
```

### 3. Create RunPod Serverless Endpoint

1. Go to [RunPod Serverless](https://www.runpod.io/console/serverless)
2. Click **"New Endpoint"**
3. Configure:
   - **Container Image**: `your-dockerhub-username/ltx2-runpod-worker:latest`
   - **GPU Type**: Select GPU with **≥48GB VRAM** (e.g., A6000, RTX 6000 Ada)
   - **Cached Model**: Enable and set to `Lightricks/LTX-2`
   - **Environment Variables**: Add all secrets from step 1
4. Deploy!

### 4. Send a Test Job

Using RunPod API:

```python
import runpod

runpod.api_key = "YOUR_RUNPOD_API_KEY"

endpoint = runpod.Endpoint("YOUR_ENDPOINT_ID")

job = endpoint.run({
    "input": {
        "mode": "t2v",
        "prompt": "A cinematic shot of a futuristic city at sunset, volumetric lighting",
        "negative_prompt": "blurry, low quality",
        "seed": 42,
        "steps": 30,
        "guidance": 7.0,
        "fps": 24,
        "num_frames": 49,
        "height": 512,
        "width": 512
    }
})

# Wait for completion
result = job.output()
print(result)
```

## Request Schema

### Text-to-Video (t2v)

```json
{
  "input": {
    "mode": "t2v",
    "prompt": "A product commercial for a luxury watch",
    "negative_prompt": "text, watermark, artifacts",
    "seed": 123,
    "steps": 30,
    "guidance": 7.0,
    "fps": 24,
    "num_frames": 49,
    "height": 512,
    "width": 512,
    "output_format": "mp4",
    "return_signed_url": true,
    "low_vram": false
  }
}
```

### Image-to-Video (i2v)

```json
{
  "input": {
    "mode": "i2v",
    "prompt": "Camera slowly zooms in on the subject",
    "image_url": "https://example.com/image.jpg",
    "seed": 456,
    "steps": 25,
    "guidance": 6.5,
    "fps": 24,
    "num_frames": 49,
    "height": 512,
    "width": 512
  }
}
```

You can also use `image_base64` instead of `image_url`:

```json
{
  "input": {
    "mode": "i2v",
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
    "prompt": "..."
  }
}
```

### All Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | `"t2v"` \| `"i2v"` | `"t2v"` | Generation mode |
| `prompt` | `string` | **required** | Text prompt |
| `negative_prompt` | `string` | `null` | Negative prompt |
| `seed` | `int` | `null` | Random seed (null = random) |
| `steps` | `int` | `30` | Inference steps |
| `guidance` | `float` | `7.0` | Guidance scale |
| `fps` | `int` | `24` | Output video FPS |
| `num_frames` | `int` | `49` | Number of frames to generate |
| `height` | `int` | `512` | Video height (pixels) |
| `width` | `int` | `512` | Video width (pixels) |
| `image_url` | `string` | `null` | Init image URL (i2v mode) |
| `image_base64` | `string` | `null` | Init image base64 (i2v mode) |
| `output_format` | `"mp4"` | `"mp4"` | Output format |
| `file_name` | `string` | `"video.mp4"` | Custom filename |
| `return_signed_url` | `bool` | `true` | Return signed URL |
| `low_vram` | `bool` | `false` | Enable CPU offload |

## Response Schema

### Success Response

```json
{
  "ok": true,
  "mode": "t2v",
  "supabase": {
    "bucket": "ltx2-outputs",
    "path": "ltx2/2026-01-13/job_abc123/video.mp4",
    "signed_url": "https://your-project.supabase.co/storage/v1/object/sign/...",
    "public_url": null
  },
  "meta": {
    "seed": 42,
    "fps": 24,
    "num_frames": 49,
    "width": 512,
    "height": 512,
    "inference_seconds": 12.34
  }
}
```

### Error Response

```json
{
  "ok": false,
  "error": "Invalid input: prompt is required"
}
```

## Performance Optimization

### 1. RunPod Cached Models (Critical!)

**Without caching**: Worker downloads 10GB+ model on every cold start (~2-5 min)  
**With caching**: Model loaded from local volume (~10-30 sec)

To enable:
1. In RunPod endpoint settings, go to **"Cached Models"**
2. Add model: `Lightricks/LTX-2`
3. RunPod will prefetch to `/runpod-volume/huggingface-cache/hub/`

The handler automatically detects cached models using the path locator:

```python
def find_cached_model_path(model_name: str) -> str | None:
    cache_name = model_name.replace("/", "--")
    snapshots_dir = os.path.join(CACHE_DIR, f"models--{cache_name}", "snapshots")
    if os.path.exists(snapshots_dir):
        snaps = sorted(os.listdir(snapshots_dir))
        if snaps:
            return os.path.join(snapshots_dir, snaps[-1])
    return None
```

### 2. Global Pipeline Loading

Pipelines are loaded **once per worker** (not per request):

```python
# ✅ Good: Outside handler (global)
engine = LTX2Engine(model_name=MODEL_NAME, model_path=MODEL_PATH)

def handler(job):
    result = engine.generate(job["input"])
```

```python
# ❌ Bad: Inside handler (reloads every request)
def handler(job):
    engine = LTX2Engine()  # Terrible for performance!
    result = engine.generate(job["input"])
```

### 3. GPU Selection

| GPU | VRAM | LTX-2 Support | Recommendation |
|-----|------|---------------|----------------|
| RTX 4090 | 24GB | ⚠️ May OOM | Use `low_vram: true` |
| A6000 | 48GB | ✅ Good | Recommended |
| A100 40GB | 40GB | ⚠️ Tight | Use lower resolutions |
| A100 80GB | 80GB | ✅ Excellent | Best performance |

**If you OOM**: Try reducing `height`, `width`, `num_frames`, or enable `low_vram: true`

### 4. Low VRAM Mode

Enable CPU offloading for memory-constrained GPUs:

```json
{
  "input": {
    "low_vram": true,
    ...
  }
}
```

**Trade-offs**:
- ✅ Reduces VRAM usage significantly
- ❌ 2-3x slower inference

## Troubleshooting

### Model not found in cache

**Symptom**: Logs show "Cached model not found, will download from HuggingFace"

**Solutions**:
1. Verify "Cached Models" is enabled in RunPod endpoint settings
2. Confirm model name is exactly `Lightricks/LTX-2`
3. Wait for model prefetch to complete (check RunPod dashboard)

### CUDA out of memory

**Symptom**: `RuntimeError: CUDA out of memory`

**Solutions**:
1. **Reduce resolution**: Try `height: 256, width: 256`
2. **Reduce frames**: Try `num_frames: 25`
3. **Enable low VRAM**: Set `low_vram: true`
4. **Use bigger GPU**: Switch to A6000 (48GB) or A100 (80GB)
5. **Lower precision**: Set `DTYPE=float16` (if not already)

### Supabase upload fails

**Symptom**: Error about bucket not found or permission denied

**Solutions**:
1. Verify bucket exists in Supabase Storage dashboard
2. Confirm `SUPABASE_SERVICE_ROLE_KEY` is the **service role** key (not anon key)
3. Check bucket policies allow server-side uploads
4. Verify `SUPABASE_URL` doesn't have trailing slash

### Diffusers version issues

**Symptom**: `ImportError: cannot import name 'LTX2Pipeline'`

**Solution**: LTX-2 may require newer diffusers. Update `requirements.txt`:

```txt
# Install from main branch
git+https://github.com/huggingface/diffusers.git
```

### Frames extraction error

**Symptom**: `RuntimeError: Could not find frames/videos in pipeline output`

**Solution**: Diffusers API may have changed. Check logs for output type and update `ltx2_engine.py`:

```python
# Add more fallbacks
if hasattr(out, "your_custom_attribute"):
    frames = out.your_custom_attribute
```

## Local Development

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...
SUPABASE_BUCKET=ltx2-outputs
```

### 3. Test Locally

```bash
# Note: This will download the model if not cached locally
python handler.py
```

Then send test job via RunPod's local testing method or by modifying `handler.py` to load `test_input.json` directly.

## Project Structure

```
ltx2-runpod-worker/
├── Dockerfile              # Container image definition
├── requirements.txt        # Python dependencies
├── handler.py              # RunPod entrypoint
├── src/
│   ├── __init__.py
│   ├── config.py           # Settings (env vars)
│   ├── schema.py           # Pydantic models (input/output)
│   ├── ltx2_engine.py      # Main generation logic
│   ├── supabase_uploader.py # Storage integration
│   ├── utils_images.py     # Image loading utilities
│   └── utils_media.py      # Video encoding utilities
├── test_input.json         # Sample request
├── README.md               # This file
└── .gitignore
```

## Future Enhancements

- [ ] **Video-to-video (v2v)**: Add init video support
- [ ] **Webhook callbacks**: Notify external API on completion
- [ ] **Progress updates**: Use RunPod progress API for long jobs
- [ ] **Batch generation**: Multiple prompts per job
- [ ] **Audio generation**: If LTX-2 supports it
- [ ] **Frame interpolation**: Increase FPS post-generation

## Resources

- [RunPod Serverless Docs](https://docs.runpod.io/serverless/overview)
- [RunPod Cached Models](https://docs.runpod.io/serverless/endpoints/model-caching)
- [Diffusers LTX-2 Docs](https://huggingface.co/docs/diffusers/main/api/pipelines/ltx2)
- [LTX-2 Model Card](https://huggingface.co/Lightricks/LTX-2)
- [Supabase Storage API](https://supabase.com/docs/guides/storage)

## License

MIT (or your preferred license)

## Contributing

Contributions welcome! Please open an issue or PR.

---

**Built with ❤️ for the RunPod community**
