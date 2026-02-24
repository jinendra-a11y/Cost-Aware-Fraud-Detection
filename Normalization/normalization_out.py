import json
from pathlib import Path
import importlib.util
from langchain_groq import ChatGroq

# Load root config.py directly to avoid local package name collisions
ROOT_CONFIG_PATH = Path(__file__).parent.parent / "config.py"
spec = importlib.util.spec_from_file_location("root_config", str(ROOT_CONFIG_PATH))
root_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(root_config)

LLM_NORMALIZATION_MODEL = root_config.LLM_NORMALIZATION_MODEL
NORMALIZE_PROMPT_FILE = root_config.NORMALIZE_PROMPT_FILE
GROQ_API_KEY = getattr(root_config, "GROQ_API_KEY", None)

# Load prompt file
with open(NORMALIZE_PROMPT_FILE, "r") as f:
    SYSTEM_PROMPT = f.read()

llm_norm = ChatGroq(
    model=LLM_NORMALIZATION_MODEL,
    temperature=0,
    top_p=1,
    api_key=GROQ_API_KEY,
)

def normalize_bills_batch(ocr_texts: list[str]) -> list[dict]:
    payload = {"raw_bill_inputs": ocr_texts}

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload)},
    ]

    response = llm_norm.invoke(messages)
    content = response.content


    # Normalize python literals if model leaks them
    content = (
        content.replace("None", "null")
               .replace("True", "true")
               .replace("False", "false")
    )

    try:
        data = json.loads(content)

    except json.JSONDecodeError:
        # Fallback: extract first JSON object/array
        start_obj = content.find("{")
        start_arr = content.find("[")

        if start_arr != -1 and (start_obj == -1 or start_arr < start_obj):
            start = start_arr
            end = content.rfind("]") + 1
        else:
            start = start_obj
            end = content.rfind("}") + 1

        data = json.loads(content[start:end])

    # Always return list[dict]
    if isinstance(data, dict):
        data = [data]

    return data

if __name__ == "__main__":
    with open ("OCR/ocr_output.json", 'r') as f:
        ocr_data = json.load(f)
    ocr_texts = [item["ocr_text"] for item in ocr_data]
    normalized_bills = normalize_bills_batch(ocr_texts)

    for bill in normalized_bills:
        bill['bill_id'] = ocr_data[normalized_bills.index(bill)]["bill_id"]
    with open("Normalization/actual_model_out.json", 'w') as f:
        json.dump(normalized_bills, f, indent=2)