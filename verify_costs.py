import os
import django
import sys
from decimal import Decimal

# Add current directory to path
sys.path.append(os.getcwd())

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from analytics.models import ProviderModel, PricingTier, UsageLog
from analytics.utils import record_usage
from providers.base import ProviderResponse
from jobs.models import Job

def test_cost_calculation():
    print("Testing Cost Calculation...")
    
    # Clear existing logs for these models to have clean test
    UsageLog.objects.filter(model__model_identifier__startswith="test-").delete()
    PricingTier.objects.filter(provider_model__model_identifier__startswith="test-").delete()
    ProviderModel.objects.filter(model_identifier__startswith="test-").delete()

    # 1. Setup Test Data
    from django.utils import timezone
    job, _ = Job.objects.get_or_create(
        job_id="test_cost_job",
        defaults={
            'pickup_location': 'Point A',
            'drop_location': 'Point B',
            'pickup_time': timezone.now(),
            'drop_time': timezone.now()
        }
    )
    
    # Create OCR Model
    ocr_model = ProviderModel.objects.create(
        name='Test OCR',
        model_identifier="test-ocr",
        provider_type='OCR'
    )
    # Tiers for OCR: 
    # 1-1000: $1.00 per 1000 requests
    # 1001-5000: $0.50 per 1000 requests
    PricingTier.objects.create(provider_model=ocr_model, range_start=1, range_end=1000, cost_per_1000_requests=Decimal('1.00'))
    PricingTier.objects.create(provider_model=ocr_model, range_start=1001, range_end=5000, cost_per_1000_requests=Decimal('0.50'))
    
    # Create LLM Model
    llm_model = ProviderModel.objects.create(
        name='Test LLM', 
        model_identifier="test-llm",
        provider_type='LLM',
        input_cost_per_million=Decimal('2.00'),
        output_cost_per_million=Decimal('5.00')
    )
    # Tiers for LLM:
    # 1-∞: $0.10 per 1000 requests
    PricingTier.objects.create(provider_model=llm_model, range_start=1, range_end=None, cost_per_1000_requests=Decimal('0.10'))

    # 2. Test OCR Cost
    # First call (request 1) -> tier 1 ($1/1k) -> $0.001
    resp_ocr = ProviderResponse(content="", input_units=1, output_units=0, model_name="test-ocr")
    cost1 = record_usage(job.job_id, resp_ocr)
    print(f"OCR Call 1 Cost: {cost1} (Expected: 0.001000)")

    # Simulate 1000 more calls to move to tier 2 (total 1001 calls)
    # Actually if we want Call 1002, we need 1001 logs already.
    # We already have 1 log from Call 1.
    logs = [UsageLog(job=job, model=ocr_model, total_cost=0) for _ in range(1000)]
    UsageLog.objects.bulk_create(logs)
    
    # Next call (request 1002) -> tier 2 ($0.5/1k) -> $0.0005
    cost2 = record_usage(job.job_id, resp_ocr)
    print(f"OCR Call 1002 Cost: {cost2} (Expected: 0.000500)")

    # 3. Test LLM Cost
    # Call 1: 1M input, 1M output -> 2.00 + 5.00 + 0.0001 (api call) = 7.0001
    resp_llm = ProviderResponse(content="", input_units=1000000, output_units=1000000, model_name="test-llm")
    cost3 = record_usage(job.job_id, resp_llm)
    print(f"LLM Call Cost: {cost3} (Expected: 7.000100)")

    print("Cleanup...")
    UsageLog.objects.filter(model__model_identifier__startswith="test-").delete()
    PricingTier.objects.filter(provider_model__model_identifier__startswith="test-").delete()
    ProviderModel.objects.filter(model_identifier__startswith="test-").delete()

if __name__ == "__main__":
    test_cost_calculation()
