import json
import logging
from typing import List, Dict, Any
from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer

from providers.factory import ProviderFactory
from analytics.utils import record_usage
from .models import Job
from .rules_check import run_rule_engine

logger = logging.getLogger(__name__)

ACCESS_TRAVEL_TYPES = [
    "Bus Ticket",
    "Train Ticket",
    "Metro Ticket",
    "Taxi Bill",
    "Other Bill",
]

CRITICAL_CONSTRAINTS = [
    "INSUFFICIENT_DATE_DATA",
    "INSUFFICIENT_AMOUNT_DATA",
    "INVALID_DATETIME_FORMAT",
    "BILL_TOTAL_MISMATCH",
    "BILL_AMOUNT_UNREASONABLE",
    "BILL_CURRENCY_MISMATCH",
    "TIME_OUTSIDE_JOB_WINDOW",
    "ACCESS_TRAVEL_DATE_TOO_FAR",
    "BILL_AMOUNT_UNACCEPTABLE",
    "BILL_LOCATION_UNREASONABLE"
]

CRITICAL_TIME_CONSTRAINTS = [
    "TIME_OUTSIDE_JOB_WINDOW",
    "ACCESS_TRAVEL_DATE_TOO_FAR"
]


class ExpensePipelineService:

    async def _ensure_job(self, job_id: str):
        if not hasattr(self, 'job_obj'):
            self.job_obj = await sync_to_async(Job.objects.get)(job_id=job_id)

    def __init__(self, job_id: str, job_obj=None):
        self.job_id = job_id
        if job_obj:
            self.job_obj = job_obj
        self.ocr_provider = ProviderFactory.get_ocr_provider()
        self.llm_provider = ProviderFactory.get_llm_provider()
        self.channel_layer = get_channel_layer()

    async def update_job_status(self, status: str, progress: int, result=None):
        """Updates DB and broadcasts via WebSockets."""
        self.job_obj.status = status
        self.job_obj.progress = progress
        if result:
            self.job_obj.final_result = result

        await sync_to_async(self.job_obj.save)()

        # Broadcast to the WebSocket group 'job_{job_id}'
        await self.channel_layer.group_send(
            f"job_{self.job_obj.job_id}",
            {
                "type": "job_update",
                "status": status,
                "progress": progress,
                "result": result
            }
        )
        logger.info(f"Job {self.job_obj.job_id}: {status} ({progress}%)")

    def _clean_json_content(self, content: str) -> str:
        """Removes markdown code blocks if present."""
        import re
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return content.strip()

    def _parse_llm_json(self, content: str) -> Any:
        cleaned = self._clean_json_content(content)

        # Normalize Python literals that LLMs sometimes produce
        cleaned = (
            cleaned.replace("None", "null")
                   .replace("True", "true")
                   .replace("False", "false")
        )

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Smart bracket-search fallback: find the outermost JSON array or object
            start_obj = cleaned.find("{")
            start_arr = cleaned.find("[")

            if start_arr != -1 and (start_obj == -1 or start_arr < start_obj):
                slice_start = start_arr
                slice_end = cleaned.rfind("]") + 1
            elif start_obj != -1:
                slice_start = start_obj
                slice_end = cleaned.rfind("}") + 1
            else:
                logger.error(f"Failed to parse LLM output: {cleaned[:100]}...")
                return []

            try:
                return json.loads(cleaned[slice_start:slice_end])
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM output (fallback): {cleaned[:100]}...")
                return []

    async def run_pipeline(self, image_paths: List[str], job_details: Dict[str, Any], mode: str = "PRODUCTION"):
        try:
            await self._ensure_job(self.job_id)

            # --- STEP 1: OCR ---
            await self.update_job_status("PROCESSING_OCR", 20)
            raw_texts = []
            for path in image_paths:
                ocr_resp = await self.ocr_provider.extract_text(path)
                await sync_to_async(record_usage)(self.job_obj.job_id, ocr_resp)
                raw_texts.append(ocr_resp.content)

            # --- STEP 2: NORMALIZATION ---
            await self.update_job_status("NORMALIZING", 40)
            norm_resp = await self.llm_provider.normalize_bills(raw_texts)
            await sync_to_async(record_usage)(self.job_obj.job_id, norm_resp)

            normalized_bills = self._parse_llm_json(norm_resp.content)
            if not isinstance(normalized_bills, list):
                normalized_bills = []

            # Map bill_id to filename for tracking
            if isinstance(normalized_bills, list) and len(normalized_bills) == len(image_paths):
                import os
                from urllib.parse import quote
                for i, bill in enumerate(normalized_bills):
                    if isinstance(bill, dict):
                        full_path = image_paths[i]
                        # Keep bill_id as a unique identifier for rule engine lookups,
                        # but also provide a UI-friendly name and an image URL.
                        display_name = os.path.basename(full_path) if isinstance(full_path, str) else str(full_path)
                        bill["bill_id"] = full_path
                        bill["display_name"] = display_name
                        bill["filename"] = display_name
                        bill["file_path"] = full_path
                        bill["image_url"] = f"/api/jobs/file?path={quote(str(full_path), safe='/')}"
            print(f"Normalized Bills: {normalized_bills}")

            # Save intermediate normalized bills
            self.job_obj.normalized_bills = normalized_bills
            await sync_to_async(self.job_obj.save)()

            # --- STEP 3: RULE CHECK ---
            await self.update_job_status("RUNNING_RULES", 60)
            rule_results = await run_rule_engine(normalized_bills, job_details)

            # --- STEP 4: BUILD FINAL RESULTS (No LLM Fraud — on hold) ---
            early_fail = []
            pass_to_llm = []

            for bill in normalized_bills:
                if not isinstance(bill, dict):
                    continue

                bill_id = bill.get("bill_id")
                bill_type = bill.get("bill_type")
                fails = rule_results.get("per_bill", {}).get(bill_id, [])

                if any(f in CRITICAL_CONSTRAINTS and f is not None for f in fails):
                    reasoning= []
                    if "INSUFFICIENT_DATE_DATA" in fails:
                        reasoning.append("Insufficient date data to evaluate the bill.") 
                    if "INSUFFICIENT_AMOUNT_DATA" in fails:
                        reasoning.append("Insufficient amount data to evaluate the bill.")
                    if "BILL_TOTAL_MISMATCH" in fails:
                        reasoning.append("The bill total does not match the sum of itemized amounts.")
                    if "BILL_AMOUNT_UNREASONABLE" in fails:
                        reasoning.append("The bill amount is unreasonable compared to typical expenses.")
                    if "TIME_OUTSIDE_JOB_WINDOW" in fails:
                        reasoning.append("The bill date is outside the job's pickup and drop-off times.")
                    if "ACCESS_TRAVEL_DATE_TOO_FAR" in fails:
                        reasoning.append("The bill date is too far from the pickup date for access travel.")
                    if "BILL_CURRENCY_MISMATCH" in fails:
                        reasoning.append("The bill currency does not match the expected currency (GBP).")
                    if "INVALID_DATETIME_FORMAT" in fails:
                        reasoning.append("The bill date is in an invalid format.")
                    if "BILL_LOCATION_UNREASONABLE" in fails:
                        reasoning.append("The bill location is unreasonable compared to the job's pickup and drop locations.")
                    if "BILL_AMOUNT_UNACCEPTABLE" in fails:
                        reasoning.append("The bill amount is unacceptable (zero or negative).")
                        
                    early_fail.append({
                        "bill_id": bill.get("display_name") or bill["bill_id"],
                        "file_path": bill.get("file_path"),
                        "image_url": bill.get("image_url"),
                        "bill_type": bill.get("bill_type"),
                        "fraud_decision": "Yes",
                        "confidence_score": 100,
                        "time_check": "Pass" if not any(f in CRITICAL_TIME_CONSTRAINTS for f in fails) else "Fail",
                        "location_check": "Review" if bill.get("bill_type") in ACCESS_TRAVEL_TYPES else ("Pass" if "BILL_LOCATION_UNREASONABLE" not in fails else "Fail"),
                        "failed_constraints": fails,
                        "reasoning": reasoning
                    })
                else:
                    if fails == [None]:
                        fails = []
                    pass_to_llm.append({    
                        "bill_id": bill.get("display_name") or bill["bill_id"],
                        "file_path": bill.get("file_path"),
                        "image_url": bill.get("image_url"),
                        "bill_type": bill.get("bill_type"),
                        "fraud_decision": "No",
                        "confidence_score": 100,
                        "time_check": "Pass",
                        "location_check": "Pass" if bill.get("bill_type") not in ACCESS_TRAVEL_TYPES else "Review",
                        "failed_constraints": fails,
                        "reasoning": ["No critical constraints failed."]
                    })

            final_output = early_fail + pass_to_llm
            await self.update_job_status("COMPLETED", 100, result=final_output)

            return final_output

        except Exception as e:
            await self.update_job_status("FAILED", 0, result={"error": str(e)})
            raise e