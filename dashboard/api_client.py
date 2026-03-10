import requests
import json
import websockets
import os

BACKEND_URL = os.getenv("BACKEND_URL")
BASE = BACKEND_URL + "/api"

def submit_job(job_details: dict, file_paths: list) -> dict:
    """Submit a job with files to the Django backend using requests library."""
    try:
        # Prepare files for multipart upload
        files = []
        for file_obj in file_paths:
            if isinstance(file_obj, dict):
                # NiceGUI format: {"name": str, "content": bytes}
                filename = file_obj["name"]
                content = file_obj["content"]
                files.append(("files", (filename, content)))
            else:
                # File-like object with .name attribute
                filename = getattr(file_obj, "name", "unknown")
                files.append(("files", (filename, file_obj)))
        
        data = {
            "job_details": json.dumps(job_details),
            "mode": job_details.get("mode", "PRODUCTION")
        }
        
        print(f"Submitting to: {BASE}/api/jobs/submit-job")
        print(f"Data: {data}")
        print(f"Files count: {len(files)}")
        
        response = requests.post(
            f"{BASE}/api/jobs/submit-job",
            data=data,
            files=files,
            timeout=60
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        return response.json()
    except Exception as e:
        print(f"Error in submit_job: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise

async def watch_job(job_id: str, on_update):
    """Watch job progress via WebSocket."""
    uri = f"ws://localhost:8000/ws/job/{job_id}/"
    try:
        async with websockets.connect(uri) as ws:
            async for msg in ws:
                await on_update(json.loads(msg))
    except Exception as e:
        await on_update({"error": str(e)})

def fetch_analytics() -> dict:
    """Fetch analytics data from the Django backend."""
    r = requests.get(f"{BASE}/api/jobs/analytics/")
    return r.json()
