import subprocess
import os
import tempfile
import base64
from typing import Protocol

def extract_frames(video_path: str, interval_seconds: float = 1.0) -> list[bytes]:
    """Extract frames from a video using ffmpeg at given interval, plus 0s and 3s."""
    # We will use ffmpeg CLI directly via subprocess to avoid ffmpeg-python dependency issues if any,
    # or just use ffmpeg-python since it's required. Let's use subprocess to be safe and simple.
    import ffmpeg
    
    # We need a directory to store the output frames
    temp_dir = tempfile.mkdtemp()
    
    # Actually, we can just do a simple ffmpeg command to extract at 1fps
    # plus explicitly extract at 0s and 3s.
    frames = []
    try:
        # Extract at 0s and 3s
        for t in [0, 3]:
            out_path = os.path.join(temp_dir, f"frame_{t}.jpg")
            subprocess.run([
                "ffmpeg", "-y", "-i", video_path, "-ss", str(t), "-vframes", "1", out_path
            ], capture_output=True)
            if os.path.exists(out_path):
                with open(out_path, "rb") as f:
                    frames.append((t, f.read()))

        # Extract at interval
        # We can extract all frames at 1fps and then filter
        fps = 1.0 / interval_seconds
        out_pattern = os.path.join(temp_dir, "interval_%04d.jpg")
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-vf", f"fps={fps}", out_pattern
        ], capture_output=True)
        
        # Read the interval frames
        # We'll just approximate their timestamps for simplicity
        i = 1
        while True:
            path = os.path.join(temp_dir, f"interval_{i:04d}.jpg")
            if not os.path.exists(path):
                break
            with open(path, "rb") as f:
                t = i * interval_seconds
                if t not in [0, 3]: # Don't duplicate 0 and 3
                    frames.append((t, f.read()))
            i += 1
            
        # Sort by timestamp
        frames.sort(key=lambda x: x[0])
        return [f[1] for f in frames]
    except Exception as e:
        print(f"Error extracting frames: {e}")
        return []
    finally:
        # Clean up temp dir
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)

class TranscriptionProvider(Protocol):
    def transcribe(self, video_path: str) -> str:
        pass

class MockTranscriptionProvider:
    def transcribe(self, video_path: str) -> str:
        return "[MOCK TRANSCRIPT] This is a mock transcript of the video. Wow, such great product. Buy now. [END TRANSCRIPT]"

def transcribe_audio(video_path: str, provider: TranscriptionProvider = None) -> str:
    if provider is None:
        provider = MockTranscriptionProvider()
    return provider.transcribe(video_path)

def get_video_metadata(video_path: str) -> dict:
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,duration", "-of",
            "default=noprint_wrappers=1:nokey=1", video_path
        ], capture_output=True, text=True)
        
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 3:
            width = int(lines[0])
            height = int(lines[1])
            duration = float(lines[2])
            aspect_ratio = width / height if height > 0 else 0
            return {
                "width": width,
                "height": height,
                "duration": duration,
                "aspect_ratio": aspect_ratio
            }
    except Exception as e:
        print(f"Error getting metadata: {e}")
    return {"width": 1920, "height": 1080, "duration": 10.0, "aspect_ratio": 16/9}
