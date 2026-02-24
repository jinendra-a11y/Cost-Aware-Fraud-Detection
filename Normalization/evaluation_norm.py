import json
import difflib
import importlib.util
from pathlib import Path

ROOT_CONFIG_PATH = Path(__file__).parent.parent / "config.py"
spec = importlib.util.spec_from_file_location("root_config", str(ROOT_CONFIG_PATH))
root_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(root_config)

NORMALIZATION_GROUND_TRUTH_FILE  = root_config.NORMALIZATION_GROUND_TRUTH_FILE
NORMALIZATION_OUTPUT_FILE = root_config.NORMALIZATION_OUTPUT_FILE

def text_similarity(str1, str2):
    """Calculates how close two strings are (0.0 to 1.0)"""
    if not str1 and not str2:
        return 1.0 if str1 == str2 else 0.0
    return difflib.SequenceMatcher(None, str(str1).lower().strip(), str(str2).lower().strip()).ratio()

def evaluate_normalization(ground_truth_file, model_output_file):
    with open(ground_truth_file, 'r') as f:
        gt_data = json.load(f)
    with open(model_output_file, 'r') as f:
        model_data = json.load(f)

    total_records = len(gt_data)
    results = []

    for i in range(total_records):
        gt = gt_data[i]
        # Handle cases where model might fail to return a record
        pred = model_data[i] if i < len(model_data) else {}
        
        scorecard = {
            "bill_id_match": 1.0 if gt.get("bill_id") == pred.get("bill_id") else 0.0,
            "amount_match": 1.0 if gt.get("amount") == pred.get("amount") else 0.0,
            "currency_match": 1.0 if gt.get("currency") == pred.get("currency") else 0.0,
            "vendor_similarity": text_similarity(gt.get("vendor"), pred.get("vendor")),
            "metadata_accuracy": 0.0
        }

        # Evaluate Metadata nested object
        gt_meta = gt.get("metadata", {})
        pred_meta = pred.get("metadata", {})
        if gt_meta:
            meta_hits = sum(1 for k, v in gt_meta.items() if v == pred_meta.get(k))
            scorecard["metadata_accuracy"] = meta_hits / len(gt_meta)

        results.append(scorecard)

    # Calculate Aggregates
    avg_amount_acc = sum(r["amount_match"] for r in results) / total_records
    avg_vendor_sim = sum(r["vendor_similarity"] for r in results) / total_records
    avg_meta_acc = sum(r["metadata_accuracy"] for r in results) / total_records
    
    final_score = (avg_amount_acc * 0.4) + (avg_vendor_sim * 0.3) + (avg_meta_acc * 0.3)

    print(f"--- Normalization Model Evaluation ---")
    print(f"Total Receipts Tested: {total_records}")
    print(f"Numeric Amount Accuracy: {avg_amount_acc:.2%}")
    print(f"Vendor Name Similarity: {avg_vendor_sim:.2%}")
    print(f"Metadata Field Accuracy: {avg_meta_acc:.2%}")
    print(f"---------------------------------------")
    print(f"OVERALL MODEL ACCURACY: {final_score:.2%}")

if __name__ == "__main__":
    evaluate_normalization(NORMALIZATION_GROUND_TRUTH_FILE, NORMALIZATION_OUTPUT_FILE)