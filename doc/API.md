# Cost-Aware Fraud Detection - API Documentation

## Overview

The Expense Approval System is a Django REST API built with [Django Ninja](https://django-ninja.rest-framework.com/) that processes expense bills through a cost-aware pipeline. The system extracts text from bill images via OCR, normalizes the data using LLM, detects fraud using rule-based checks, and tracks all API call costs.

**Base URL:** `http://localhost:8000/api`

**Authentication:** Not currently implemented (to be added)

---

## API Endpoints

### 1. Submit Job (Process Expense Bill)

Submit expense bills with images for processing.

#### Endpoint
```
POST /api/jobs/submit-job
```

#### Description
Submits a new job with bill images and metadata. The system will:
1. Extract text from images using OCR (Google Vision)
2. Normalize extracted text into structured bill data
3. Run fraud detection rules
4. Return job tracking ID

This is an **async endpoint** that triggers background processing.

#### Request Format

**Content-Type:** `multipart/form-data`

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `job_details` | JSON String | Yes | Job metadata as JSON string containing: |
| | | | • `job_id` (string): Unique identifier for the job |
| | | | • `pickup_location` (string): Location where trip started |
| | | | • `drop_location` (string): Location where trip ended |
| | | | • `pickup_time` (ISO 8601): Departure timestamp |
| | | | • `drop_time` (ISO 8601): Arrival timestamp |
| `files` | File[] | Yes | One or more bill/receipt images (JPG, PNG) |
| `mode` | String | No | Processing mode: `"PRODUCTION"` (default) or `"TESTING"` |

#### Example Request

**cURL:**
```bash
curl -X POST http://localhost:8000/api/jobs/submit-job \
  -F "job_details={\"job_id\": \"612034\",\"pickup_location\": \"ST4 2RS\",\"drop_location\": \"WA7 4JB\",\"pickup_time\": \"2026-01-28T10:16:16\",\ "drop_time\": \"2026-01-28T11:47:39\",\"vehicle_type\": \"Petrol\"}" \
  -F "files=@612034_1.jpg" \
  -F "files=@612034_2.jpg" \
  -F "mode=PRODUCTION"
```


**Python Requests:**
```python
import requests
from datetime import datetime

job_details = {
        "job_id": "612034",
        "pickup_location": "ST4 2RS",
        "drop_location": "WA7 4JB",
        "pickup_time": "2026-01-28T10:16:16",
        "drop_time": "2026-01-28T11:47:39",
        "vehicle_type": "Petrol"
    }

files = [
    ('files', open('612034_1.jpg', 'rb')),
    ('files', open('612034_2.jpg', 'rb'))
]

data = {
    'job_details': json.dumps(job_details),
    'mode': 'PRODUCTION'
}

response = requests.post(
    'http://localhost:8000/api/jobs/submit-job',
    files=files,
    data=data
)
print(response.json())
```

#### Response

**Status:** `200 OK`

```json
{
  "message": "Job submitted successfully",
  "job_database_id": 42
}
```

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Confirmation message |
| `job_database_id` | integer | Database primary key for tracking (use this to query job status via WebSocket) |

#### Error Responses

| Status | Code | Description |
|--------|------|-------------|
| 400 | `BadRequest` | Invalid JSON in job_details or missing required files |
| 500 | `InternalServerError` | File save error or pipeline initialization failed |

#### Processing Pipeline

The job triggers an asynchronous multi-stage pipeline:

1. **OCR Stage** - Extract text from images using Google Vision API
2. **Normalization Stage** - Parse OCR output into structured bill format using Groq Llama LLM
3. **Rule Checking Stage** - Apply business logic rules (date ranges, amounts, fraud patterns)
4. **Job Completion** - Store results in database and emit WebSocket update

**Real-time Updates:** Subscribe to WebSocket channel `ws://localhost:8000/ws/job/{job_id}/` for live status updates.

---

### 2. Get Analytics

Retrieve cost analytics and API usage statistics.

#### Endpoint
```
GET /api/jobs/analytics/
```

#### Description
Returns aggregated cost metrics across all jobs, broken down by:
- Provider (Groq, Google Vision)
- Model used (e.g., llama-3.1-8b, llama-3.3-70b)
- Per-job cost breakdown

This data is gathered from the `UsageLog` model which tracks every API call.

#### Request Parameters

None

#### Example Request

**cURL:**
```bash
curl -X GET http://localhost:8000/api/jobs/analytics/
```

**Python:**
```python
import requests

response = requests.get('http://localhost:8000/api/jobs/analytics/')
analytics = response.json()
print(f"Total Cost: ${analytics['combined_total']}")
```

#### Response

**Status:** `200 OK`

```json
{
  "groq_normalization": {
    "calls": 45,
    "tokens_in": 125000,
    "tokens_out": 87500,
    "total_cost": "12.50"
  },
  "groq_fraud": {
    "calls": 0,
    "tokens_in": 0,
    "tokens_out": 0,
    "total_cost": "0.00"
  },
  "google_vision": {
    "calls": 50,
    "images": 120,
    "tokens_in": 0,
    "tokens_out": 0,
    "total_cost": "2.40"
  },
  "combined_total": "14.90",
  "per_job": [
    {
      "job_id": "JOB123",
      "created_at": "2025-12-20T14:30:00Z",
      "job_total": "0.35"
    },
    {
      "job_id": "JOB122",
      "created_at": "2025-12-20T13:45:00Z",
      "job_total": "0.28"
    }
  ]
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `groq_normalization` | object | Cost breakdown for Groq Llama (normalization model) |
| `groq_normalization.calls` | integer | Number of API calls made |
| `groq_normalization.tokens_in` | integer | Total input tokens consumed |
| `groq_normalization.tokens_out` | integer | Total output tokens generated |
| `groq_normalization.total_cost` | string | Total cost in USD (as string for precision) |
| `groq_fraud` | object | Cost breakdown for Groq Fraud Detection (currently unused) |
| `google_vision` | object | Cost breakdown for Google Vision OCR |
| `google_vision.images` | integer | Number of images processed (instead of tokens) |
| `combined_total` | string | Sum of all costs in USD |
| `per_job` | array | List of recent jobs (last 10) with individual costs |
| `per_job[].job_id` | string | Job identifier |
| `per_job[].created_at` | string | Job creation timestamp (ISO 8601) |
| `per_job[].job_total` | string | Cost for that specific job in USD |

#### Error Responses

| Status | Code | Description |
|--------|------|-------------|
| 500 | `InternalServerError` | Database connection error |

---

## Data Models

### Job
Represents a single expense approval task.

```python
{
  "id": 1,                              # Database primary key
  "job_id": "612034",
  "pickup_location": "ST4 2RS",
  "drop_location": "WA7 4JB",
  "pickup_time": "2026-01-28T10:16:16",
  "drop_time": "2026-01-28T11:47:39",
  "vehicle_type": "Petrol"
  "status": "COMPLETED",                # QUEUED | PROCESSING | COMPLETED | FAILED
  "progress": 100,                      # 0-100% completion
  "created_at": "2025-12-20T14:30:00Z",
  "updated_at": "2025-12-20T14:35:00Z",
  "final_result": { ... },              # Processed bills and decisions
  "normalized_bills": [ ... ]           # Intermediate normalized data
}
```

**Status Values:**
- `QUEUED` - Job received, awaiting processing
- `PROCESSING` - Currently being processed
- `COMPLETED` - Successfully finished
- `FAILED` - Processing failed

### UsageLog
Tracks every individual API call and its cost.

```python
{
  "id": 1,
  "job_id": 612034,                          # Foreign key to Job
  "model": {
    "model_identifier": "llama-3.1-8b-instant",
    "name": "Groq",
    "provider_type": "LLM"
  },
  "input_units": 5000,                  # Tokens or images
  "output_units": 2500,
  "input_cost": "0.00025",
  "output_cost": "0.00075",
  "api_call_cost": "0.00",              # Per-call fee if applicable
  "total_cost": "0.001",                # Sum of above
  "timestamp": "2025-12-20T14:30:30Z"
}
```

### ProviderModel
Defines pricing for available models.

```python
{
  "id": 1,
  "name": "Groq",
  "model_identifier": "llama-3.1-8b-instant",
  "provider_type": "LLM",
  "input_cost_per_million": 0.05,
  "output_cost_per_million": 0.15
}
```

---

## Processing Pipeline

### Architecture

```
USER SUBMITS JOB
    ↓
[submit-job endpoint]
    ├─→ Create Job record (status=QUEUED)
    ├─→ Save files to disk
    └─→ Trigger async pipeline (asyncio.create_task)
              ↓
         [ExpensePipelineService]
              ├─→ OCR (Google Vision)
              │   • Extract text from images
              │   • Log cost in UsageLog
              │
              ├─→ Normalization (Groq Llama)
              │   • Parse OCR output
              │   • Generate structured bill JSON
              │   • Log cost
              │
              ├─→ Rule Checking
              │   • Validate bill amounts
              │   • Check timestamp constraints
              │   • Detect fraud patterns
              │   • Generate approval decision
              │
              └─→ Save Results
                  • Store final_result in Job
                  • Update status=COMPLETED
                  • Broadcast via WebSocket
```

### Cost-Aware Decisions

The system makes provider selection decisions based on:
- **Critical rule failures** → Skip expensive secondary models, mark as rejected
- **Non-critical failures** → Use cheaper normalization model first
- **High confidence rules** → Avoid fraud detection model calls when possible

---

## Configuration

Configuration is read from environment variables in [config.py](config.py):

```python
# Provider credentials
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GOOGLE_APPLICATION_CREDENTIALS_JSON = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

# Render runtime (recommended)
# Set PYTHON_VERSION=3.12.0 to avoid Python 3.14 incompatibilities in some dependencies.
PYTHON_VERSION = os.getenv("PYTHON_VERSION")

# Feature flags
ENABLE_FRAUD_DETECTION = os.getenv("ENABLE_FRAUD_DETECTION", "false").lower() == "true"
ENABLE_FRAUD_DETECTION_MODEL = os.getenv("ENABLE_FRAUD_DETECTION_MODEL", "true").lower() == "true"

# Cost-aware settings
COST_AWARE_THRESHOLD = float(os.getenv("COST_AWARE_THRESHOLD", "0.05"))  # Skip fraud check if cost > $0.05
```

### Google Vision auth on Render (recommended)

On Render, it’s often easiest to avoid shipping a service-account key file. Set `GOOGLE_APPLICATION_CREDENTIALS_JSON` to the full JSON contents of your service account key. The app will use it directly (no filesystem dependency).

---

## Error Handling

### Common Error Scenarios

| Scenario | Status | Response |
|----------|--------|----------|
| Missing `job_details` | 400 | `{"detail": "job_details is required"}` |
| Invalid JSON in `job_details` | 400 | `{"detail": "Invalid JSON"}` |
| No files uploaded | 400 | `{"detail": "At least one file is required"}` |
| File save permission error | 500 | `{"detail": "Failed to save files"}` |
| OCR service unavailable | 500 | Job status → FAILED, error logged |
| LLM service unavailable | 500 | Job status → FAILED, error logged |

### Error Response Format

```json
{
  "detail": "Description of what went wrong"
}
```

---

## Rate Limiting

**Not currently implemented.** Recommended for production:
- Rate limit by client IP: 100 requests per minute
- Rate limit expensive endpoints: 20 per-job submissions per minute

---

## WebSocket Real-Time Updates

Subscribe to live job status updates.

### Connection

```
ws://localhost:8000/ws/job/{job_id}/
```

### Message Format (from server)

```json
{
  "type": "job_update",
  "status": "PROCESSING",
  "progress": 50,
  "result": null
}
```

### Example Client (JavaScript)

```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/job/JOB123/`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Status: ${data.status}, Progress: ${data.progress}%`);
};

ws.onerror = (event) => {
  console.error("WebSocket error:", event);
};
```

---

## Authentication & Security

### Current State
- **NO authentication** implemented
- All endpoints are publicly accessible

### Recommended for Production
1. **JWT Tokens** - Add token-based authentication
2. **CORS** - Restrict to whitelisted domains
3. **Rate Limiting** - Prevent abuse
4. **API Keys** - For programmatic access
5. **HTTPS** - All connections must be encrypted
6. **Input Validation** - Sanitize all input

---

## Testing

### Example Test Workflow

1. **Submit a job:**
```bash
curl -X POST http://localhost:8000/api/jobs/submit-job \
  -F 'job_details={"job_id":"TEST1","pickup_location":"A","drop_location":"B","pickup_time":"2025-12-15T10:00:00Z","drop_time":"2025-12-15T18:00:00Z"}' \
  -F 'files=@test_receipt.jpg'
```

2. **Monitor progress via WebSocket:**
```bash
wscat -c ws://localhost:8000/ws/job/TEST1/
```

3. **Check analytics:**
```bash
curl -X GET http://localhost:8000/api/jobs/analytics/ | python -m json.tool
```

---

## Performance Metrics

### Typical Response Times

| Operation | Duration | Notes |
|-----------|----------|-------|
| Submit job (validation) | 100-200ms | Fast (only file save) |
| OCR processing | 2-5s | Per 1-3 images |
| Normalization LLM | 1-3s | Groq API call |
| Rule checking | <100ms | Local execution |
| Total pipeline | 5-15s | End-to-end |

### Cost Estimates

| Provider | Model | Cost |
|----------|-------|------|
| Google Vision | OCR | $0.48 per 1000 requests |
| Groq | llama-3.1-8b (normalization) | $0.05 per 1M input tokens, $0.15 per 1M output |
| Groq | llama-3.3-70b (fraud detection) | Higher cost, currently unused |

---

## Support

For issues or questions:
1. Check [doc/cost_aware_project.md](cost_aware_project.md) for system design
2. Review [jobs/services.py](../jobs/services.py) for pipeline logic
3. See [jobs/rules_check.py](../jobs/rules_check.py) for validation rules

---

**Last Updated:** February 2026
**API Version:** 1.0
