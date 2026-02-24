# Cost-Aware Fraud Detection — Project Overview

## 1) Fraud API (original)

The original FastAPI-based Fraud API exposed endpoints to receive transaction or invoice data, run model(s) to score the likelihood of fraud, and apply a rules-check stage to produce final pass/fail decisions and actionable flags. It served as the central inference and decision layer with logging, simple metrics, and support for asynchronous requests.

Key responsibilities:
- Receive and validate input payloads (OCR, transaction fields).
- normalize all bills in structured format using model
- Execute rule checks to map model outputs into early fail and pass to llm data.
- Run fraud detection model(s) to produce scores and features for pass to llm bills.
- Return structured fraud results for downstream workflows.

## 2) Cost-aware extension (what was added)

We extended the original project to be cost-aware: the inference pipeline now accounts for per-model and per-provider costs when choosing how to run checks and produce results. Main enhancements:
- Per-call cost tracking and simple cost estimates per provider/model.
- Selection logic to prefer lower-cost providers or smaller models when they meet accuracy/coverage constraints.
- Minimal changes to API surface — decision logic happens inside the service before invoking expensive resources.

Benefits: reduced inference spend, predictable cost behavior, and the ability to tune cost-vs-accuracy tradeoffs.

## 3) Removal of the second fraud model (why)

We removed the previously-used second fraud model because the pipeline’s rule-check stage now consistently covers the decision logic needed for production results. In practice, the extra model:
- Provided overlapping signals already captured by rules and the primary model.
- Increased latency and cost without improving pass/fail coverage.

Reasoning summary:
- The rule-checks (business rules + derived features) achieved the required decision coverage, making the second model redundant.
- Removing it simplified the pipeline, lowered costs, and reduced operational complexity while preserving decision quality.

Rule-check constraints (exact checks implemented):
- Mandatory fields: `bill_type`, `bill_date_time`, `amount`, `currency`, `vendor`, `location` — missing fields produce `INSUFFICIENT_DATA`.
- Currency must be `GBP` — otherwise `BILL_CURRENCY_MISMATCH`.
- Amount sanity: numeric and > 0 — otherwise `INSUFFICIENT_DATA` or `BILL_AMOUNT_UNACCEPTABLE`.
- Duplicate detection by signature (`bill_type`, `bill_date_time`, `amount`, `vendor`) — duplicates are recorded.
- Total consistency: sum of `line_items` vs `amount` with 5% tolerance — `BILL_TOTAL_MISMATCH` or `INSUFFICIENT_DATA`.
- Time validation:
	- For travel tickets (`Bus Ticket`, `Train Ticket`, `Metro Ticket`, `Taxi Bill`, `Other Bill`): if `amount` > 10 → `BILL_AMOUNT_UNREASONABLE`; if bill date differs from pickup by >1 day → `ACCESS_TRAVEL_DATE_TOO_FAR`.
	- For other bills: bill datetime must fall between job `pickup_time` and `drop_time` → `TIME_OUTSIDE_JOB_WINDOW`.

Additional constraints surfaced in `jobs/services.py` and used as critical checks:
- `INSUFFICIENT_DATE_DATA`, `INSUFFICIENT_AMOUNT_DATA`, `INVALID_DATETIME_FORMAT`, `BILL_LOCATION_UNREASONABLE`.

How constraints are used in the pipeline (behavior):
- The service collects rule results from `run_rule_engine` (per-bill fails and duplicates) and treats a set of labels as `CRITICAL_CONSTRAINTS`.
- If any critical constraint appears for a bill, the pipeline marks the bill as an `early_fail` with:
	- `fraud_decision: Yes`, `confidence_score: 100`, `failed_constraints` (list), and human-readable `reasoning` entries for each failed constraint.
	- `time_check` is set to `Fail` if any `CRITICAL_TIME_CONSTRAINTS` (`TIME_OUTSIDE_JOB_WINDOW`, `ACCESS_TRAVEL_DATE_TOO_FAR`) exist; otherwise `Pass`.
	- `location_check` is `Review` for access-travel bill types, or `Fail`/`Pass` based on `BILL_LOCATION_UNREASONABLE`.
- Bills without critical constraints are queued as `pass_to_llm` (no immediate LLM fraud model is used currently).

Implementation notes:
- The service maps normalization outputs to filenames and stores `bill_id`, `filename`, and `file_path` on normalized bills for tracking.
- The normalization harness and `jobs/rules_check.py` supply the inputs to these checks; `jobs/services.py` contains the final decision logic and reasoning mapping.

(See `jobs/rules_check.py` and `jobs/services.py` for the authoritative implementation.)

## Pros of the current cost-aware design
- Lower operational and inference costs.
- Faster end-to-end response times (fewer model calls).
- Simpler maintenance and fewer moving parts.
- Clearer telemetry: cost vs. decision outcome is observable and actionable.

If future coverage gaps appear, the design allows reintroducing lightweight specialized models behind cost/accuracy gates.

---
## 4) Normalization & OCR testing framework

What exists now:
- A `Normalization` folder with a testing harness that calls an LLM-based normalizer (`Normalization/normalization_out.py`). The harness loads prompts and model configuration from `config.py` and writes `Normalization/actual_model_out.json` for evaluation.
- An `OCR` folder and provider implementation (`providers/ocr_provider.py`) that extract raw text; `config.py` centralizes paths and model names.
- A lightweight dependency list in `requirements copy.txt` to document required packages for the testing harness.

Why this is helpful:
- Decouples experimental model evaluation from the Django app — faster iteration and safer experiments.
- `config.py` and `NORMALIZE_PROMPT` make swapping normalization models straightforward for future tests.
- The testing script evaluates model output against expected normalization (`Normalization/expected_norm_out.json`), providing a clear pass/fail baseline.

Integration guidance (short plan):
- Keep the current separate testing harness for experimentation and CI model validation.
- For production use, integrate the stable normalization step into the Django service by:
	1. Turning the normalization harness into a reusable module or Django app.
	2. Moving configuration into Django settings (or load from `config.py` once during startup).
	3. Adding a management command or REST endpoint to run normalization in-app.
	4. Adding unit tests and CI checks to validate normalization outputs before deployment.

Pros & significance:
- Faster model iteration without touching production code.
- Clear migration path to production when a model proves stable.
- Maintains separation of concerns: experiment vs. runtime.

---
Short, professional summary created per request.
