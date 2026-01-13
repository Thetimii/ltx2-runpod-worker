import os
import imageio
import numpy as np


def save_video_mp4(frames: list, out_path: str, fps: int):
    """
    Save a list of frames as an MP4 video file.
    
    Args:
        frames: List of PIL Images or numpy arrays
        out_path: Output file path
        fps: Frames per second
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    writer = imageio.get_writer(out_path, fps=fps, codec="libx264", quality=8)
    try:
        for f in frames:
            # Convert PIL Image to numpy array if needed
            if hasattr(f, "convert"):
                arr = np.array(f.convert("RGB"))
            else:
                arr = np.array(f)
            writer.append_data(arr)
    finally:
        writer.close()
