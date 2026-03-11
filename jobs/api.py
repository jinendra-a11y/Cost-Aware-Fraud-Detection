import json
import os
import uuid
from typing import List
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404
from ninja import Router, File, Form
from ninja.files import UploadedFile
from .models import Job
from django.utils.dateparse import parse_datetime
from django.utils import timezone
import asyncio
from .services import ExpensePipelineService

router = Router()


def _parse_to_aware(dt_str: str):
    dt = parse_datetime(dt_str) if dt_str else None
    if dt and timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


@router.get("/file")
def get_uploaded_file(request, path: str):
    """
    Stream an uploaded file from Django storage.
    Kept intentionally simple for demos; restricts access to the `uploads/` prefix.
    """
    if not path or ".." in path or path.startswith(("/", "\\")) or not path.startswith("uploads/"):
        raise Http404("File not found")

    try:
        f = default_storage.open(path, "rb")
    except Exception:
        raise Http404("File not found")

    # Ensure browsers can render via <img> by sending a reasonable content-type.
    import mimetypes
    content_type, _ = mimetypes.guess_type(path)
    return FileResponse(f, content_type=content_type or "application/octet-stream")


@router.post("/submit-job")
async def submit_job(
    request,
    job_details: str = Form(...),
    mode: str = Form("PRODUCTION"),
    files: List[UploadedFile] = File(...)
):
    # 1. Parse Metadata
    details = json.loads(job_details)
    j_id = details.get("job_id")

    # 2. Create DB Record (async compat)
    from asgiref.sync import sync_to_async
    job, created = await sync_to_async(Job.objects.get_or_create)(
            job_id=j_id,
            defaults={
                "pickup_location": details.get("pickup_location", "Unknown"),
                "drop_location": details.get("drop_location", "Unknown"),
                "pickup_time": _parse_to_aware(details.get("pickup_time")),
                "drop_time": _parse_to_aware(details.get("drop_time")),
            })
    job.status = "QUEUED"
    await sync_to_async(job.save)()

    # 3. Save Files to Disk
    image_paths = []
    for f in files:
        # Use a predictable relative path
        relative_path = f"uploads/{job.id}/{f.name}"
        # Use default_storage which is configured in settings.py
        saved_path = await sync_to_async(default_storage.save)(relative_path, f)
        # Store the storage path (portable across deployments).
        image_paths.append(saved_path)

    # 4. Trigger Background Task directly using asyncio
    service = ExpensePipelineService(j_id, job_obj=job)
    asyncio.create_task(service.run_pipeline(image_paths, details, mode))

    return {"message": "Job submitted successfully", "job_database_id": job.id}


@router.get("/analytics/")
def get_analytics(request):
    """
    Get analytics data: cost breakdown by provider/model, per-job costs.
    Queries UsageLog for fine-grained cost tracking.
    """
    from django.db.models import Sum, Count
    from analytics.models import UsageLog
    import decimal

    def safe(val):
        """Convert Decimal to string for JSON serialization."""
        return str(val) if isinstance(val, decimal.Decimal) else (val or 0)

    def agg(qs):
        """Run aggregation on a UsageLog queryset."""
        r = qs.aggregate(
            calls=Count("id"),
            tokens_in=Sum("input_units"),
            tokens_out=Sum("output_units"),
            total_cost=Sum("total_cost")
        )
        return {k: safe(v) for k, v in r.items()}

    # Groq normalization (llama-3.1-8b-instant)
    groq_norm = agg(
        UsageLog.objects.filter(model__model_identifier="llama-3.1-8b-instant")
    )

    # Groq fraud (llama-3.3-70b-versatile) — currently 0 calls
    groq_fraud = agg(
        UsageLog.objects.filter(model__model_identifier="llama-3.3-70b-versatile")
    )

    # Google Vision OCR
    gcv = agg(
        UsageLog.objects.filter(model__model_identifier="google-vision-ocr")
    )
    gcv["images"] = gcv.pop("tokens_in", 0)

    # Combined total
    combined = safe(
        UsageLog.objects.aggregate(t=Sum("total_cost"))["t"]
    )

    # Per-job cost (last 10 jobs)
    per_job = list(
        Job.objects.select_related()
        .values("job_id", "created_at")
        .order_by("-created_at")[:10]
    )
    for row in per_job:
        job_obj = Job.objects.get(job_id=row["job_id"])
        total = job_obj.usage_logs.aggregate(t=Sum("total_cost"))["t"]
        row["job_total"] = safe(total)
        row["created_at"] = row["created_at"].isoformat() if row["created_at"] else None

    return {
        "groq_normalization": groq_norm,
        "groq_fraud": groq_fraud,
        "google_vision": gcv,
        "combined_total": combined,
        "per_job": per_job,
    }
