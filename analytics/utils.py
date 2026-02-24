from decimal import Decimal
from typing import TYPE_CHECKING
from .models import ProviderModel, UsageLog, PricingTier, ProviderUsage
from django.db.models import Q
from jobs.models import Job

if TYPE_CHECKING:
    from providers.base import ProviderResponse

def record_usage(job_id: str, response: 'ProviderResponse'):
    """
    Standardized utility to record API costs.
    Calculates tiered API call costs and per-million token costs for LLMs.
    """
    try:
        # 1. Fetch the pricing record for this specific model
        pricing = ProviderModel.objects.get(model_identifier=response.model_name)
        
        # 2. Calculate API Call Cost (Tiered)
        # We count total historical requests for this specific model identifier
        total_requests = UsageLog.objects.filter(model=pricing).count() + 1
        
        tier = PricingTier.objects.filter(
            provider_model=pricing,
            range_start__lte=total_requests
        ).filter(
            Q(range_end__gte=total_requests) | Q(range_end__isnull=True)
        ).first()

        api_call_cost = Decimal(0)
        if tier:
            # Pricing is per 1000 requests, so divide by 1000 for a single call cost
            api_call_cost = tier.cost_per_1000_requests / Decimal(1000)

        # 3. Calculate Input/Output Costs
        input_cost = Decimal(0)
        output_cost = Decimal(0)

        if pricing.provider_type == 'LLM':
            # LLMs are priced per million tokens
            input_cost = (Decimal(response.input_units) / Decimal(1000000)) * pricing.input_cost_per_million
            output_cost = (Decimal(response.output_units) / Decimal(1000000)) * pricing.output_cost_per_million
        # For OCR or others, input/output cost is 0, only api_call_cost applies

        total_cost = input_cost + output_cost + api_call_cost

        # 4. Create the log entry linked to the Job
        job = Job.objects.get(job_id=job_id)
        UsageLog.objects.create(
            job=job,
            model=pricing,
            input_units=response.input_units,
            output_units=response.output_units,
            input_cost=input_cost,
            output_cost=output_cost,
            api_call_cost=api_call_cost,
            total_cost=total_cost
        )

        # 5. Also update the legacy ProviderUsage model for compatibility
        ProviderUsage.objects.create(
            job=job,
            provider_name=pricing.name,
            model_used=pricing.model_identifier,
            tokens_in=response.input_units,
            tokens_out=response.output_units,
            cost_estimated=total_cost
        )
        return total_cost
        
    except ProviderModel.DoesNotExist:
        # Fallback for debugging if you haven't added the model to the Admin yet
        print(f"WARNING: No pricing found for model {response.model_name}. Recording 0 cost.")
        return Decimal(0)
    except Exception as e:
        print(f"ERROR recording analytics: {str(e)}")
        return Decimal(0)