import requests
import json
# Your list of bill filenames
bills = ["612034_1.png", "612034_2.png"]

# Construct the list of tuples
# Format: ('key_name', ('filename', file_object, 'content_type'))
files = [
    ('files', (bill, open(bill, 'rb'), 'image/png')) 
    for bill in bills
]

job_data = {
        "job_id": "612034",
        "pickup_location": "ST4 2RS",
        "drop_location": "WA7 4JB",
        "pickup_time": "2026-01-28T10:16:16",
        "drop_time": "2026-01-28T11:47:39",
        "vehicle_type": "Petrol"
    }

payload = {
    'job_details': json.dumps(job_data) 
}

# When sending the request, 'files' takes the list of tuples
response = requests.post(
    "http://127.0.0.1:8000/api/jobs/submit-job", 
    data=payload, # Example job details
    files=files
)

try:
    print(response.json())
except requests.exceptions.JSONDecodeError:
    print("❌ ERROR: Server did not return JSON!")
    print(f"Status Code: {response.status_code}")
    print("--- RAW RESPONSE START ---")
    print(response.text) # This will likely show a Django 500 or 404 HTML page
    print("--- RAW RESPONSE END ---")