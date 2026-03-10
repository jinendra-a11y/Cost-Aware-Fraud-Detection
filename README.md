# Cost-Aware Fraud Detection

Short, production-oriented pipeline for OCR → normalization → rule checks → decisioning with cost-aware inference policy.

**Key pieces**
- Project overview: [doc/cost_aware_project.md](doc/cost_aware_project.md#L1)
 - Project overview (design doc): [doc/cost_aware_project.md](doc/cost_aware_project.md#L1)
 - Project overview (API doc): [doc/API.md](doc/API.md#L1)
- Rule checks and pipeline logic: [jobs/rules_check.py](jobs/rules_check.py#L1) and [jobs/services.py](jobs/services.py#L1)
- Normalization test harness: [Normalization/normalization_out.py](Normalization/normalization_out.py#L1)
- OCR provider example: [providers/ocr_provider.py](providers/ocr_provider.py#L1)
- Configuration used by tests: [config.py](config.py#L1)

Quick concepts
- The system runs OCR to extract raw text, normalizes text into structured bills, then runs deterministic rule checks. Critical rule failures are treated as early-fail (no secondary model used) to reduce cost and latency.
- The cost-aware extension tracks per-call costs and prefers lower-cost providers or smaller models when accuracy constraints are satisfied.

Getting started (Windows)

1. Create and activate a virtual environment

```powershell
python -m venv env
env\Scripts\Activate.ps1   # PowerShell
```

2. Install dependencies (use `requirements copy.txt` for the normalization/test harness)

```powershell
pip install -r "requirements.txt"
```

3. Run the normalization test harness (reads `OCR/ocr_output.json` and writes `Normalization/actual_model_out.json`)(only for developer)

```powershell
python Normalization/normalization_out.py
```

4. Run Django app (if you want full pipeline in-app)

```powershell
# configure env vars (see config.py) then
python manage.py runserver
```

5. Run NiceGUI App(in another terminal)

```powershell
python dashboard/app.py
```

Notes on tests & integration
- Keep the `Normalization` harness separate for experiments; when a normalization model is validated, convert it into a reusable module or Django app and wire it into the `ExpensePipelineService` in `jobs/services.py`.
- The authoritative rule-check logic lives in `jobs/rules_check.py` and critical constraint handling is in `jobs/services.py`.

Files of interest for maintainers
- [doc/cost_aware_project.md](doc/cost_aware_project.md#L1) — concise project explanation and design notes.
- [requirements copy.txt](requirements copy.txt#L1) — dependencies for the testing harness.
- [.gitignore](.gitignore#L1) — recommended ignores created in repo.

Contributing
- Open issues or pull requests. For normalization model changes, include test inputs (`OCR/ocr_output.json`) and expected normalization outputs (`Normalization/expected_norm_out.json`).


