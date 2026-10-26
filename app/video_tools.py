"""Video generation tools for greenhouse plants using gemini-omni-flash-preview."""
import base64
import json
import re
import uuid
import urllib.request
from typing import Any, Dict

import google.auth
from google.auth.transport.requests import Request
from google.cloud import storage
from google.adk.tools import ToolContext
from google.genai import types

PROJECT_ID = "qwiklabs-gcp-03-2deba0eddfc5"
BUCKET_NAME = "greenhouse-plants-qwiklabs-gcp-03-2deba0eddfc5"


async def generate_plant_video(
    prompt: str,
    tool_context: ToolContext,
    plant_name: str = "plant",
    duration: str = "3s",
) -> Dict[str, Any]:
    """Generate a short video for a plant using Google's Omni model (gemini-omni-flash-preview).

    Saves the generated video as an artifact for the Playground's Artifacts panel,
    and uploads the video bytes to the public Cloud Storage bucket, returning its public URL.

    Args:
        prompt: Description of the video to generate (e.g. 'A time lapse of a Monstera Deliciosa leaf unfurling in morning sunlight').
        tool_context: The ADK tool context used to save the artifact in the Playground.
        plant_name: Name of the plant to use in the filename (e.g. 'Monstera Deliciosa').
        duration: Video duration, allowed between 3s and 10s (default '3s').

    Returns:
        A dictionary with the public video URL, filename, and status.
    """
    # 1. Authenticate with Google Cloud
    creds, _ = google.auth.default()
    creds.refresh(Request())

    url = f"https://aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/global/interactions"
    body = {
        "model": "gemini-omni-flash-preview",
        "input": [
            {"type": "text", "text": prompt}
        ],
        "response_format": [
            {
                "type": "video",
                "duration": duration if duration.endswith("s") else f"{duration}s",
                "aspect_ratio": "16:9",
            }
        ],
        "generation_config": {
            "video_config": {
                "task": "text_to_video"
            }
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to call gemini-omni-flash-preview: {e}",
        }

    # 2. Extract video bytes from the response steps
    video_bytes = None
    mime_type = "video/mp4"

    for step in data.get("steps", []):
        if step.get("type") == "model_output":
            for content in step.get("content", []):
                if content.get("type") == "video":
                    mime_type = content.get("mime_type", "video/mp4")
                    raw_data = content.get("data")
                    if raw_data:
                        video_bytes = base64.b64decode(raw_data)
                        break
        if video_bytes:
            break

    if not video_bytes:
        return {
            "status": "error",
            "message": "No video bytes returned by gemini-omni-flash-preview.",
        }

    # 3. Create filename
    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "-", plant_name.strip().lower())
    clean_name = re.sub(r"-+", "-", clean_name).strip("-") or "plant"
    filename = f"{clean_name}-video-{uuid.uuid4().hex[:6]}.mp4"

    # 4. Save artifact with tool_context.save_artifact (shows in Playground Artifacts panel)
    artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
    version = await tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 5. Upload bytes to public Cloud Storage bucket
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

    return {
        "status": "success",
        "plant_name": plant_name,
        "filename": filename,
        "artifact_version": version,
        "public_video_url": public_url,
        "message": f"Video generated and uploaded successfully. Public URL: {public_url}",
    }
