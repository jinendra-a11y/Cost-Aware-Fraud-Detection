from django.db import models
from jobs.models import Job

class ProviderModel(models.Model):
    """Stores the pricing for specific models (e.g., Groq Llama3, Google Vision)"""
    PROVIDER_TYPES = [('OCR', 'OCR'), ('LLM', 'LLM')]
    
    name = models.CharField(max_length=100) # e.g., 'Groq'
    model_identifier = models.CharField(max_length=100, unique=True) # e.g., 'llama3-70b-8192'
    provider_type = models.CharField(max_length=10, choices=PROVIDER_TYPES)
    
    # LLM pricing (per million tokens)
    input_cost_per_million = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    output_cost_per_million = models.DecimalField(max_digits=12, decimal_places=6, default=0)


    def __str__(self):
        return f"{self.name} - {self.model_identifier}"

class PricingTier(models.Model):
    """Tiered pricing for API calls, e.g., per 1000 requests"""
    provider_model = models.ForeignKey(ProviderModel, on_delete=models.CASCADE, related_name='tiers')
    range_start = models.IntegerField(help_text="Start of request range (e.g., 1)")
    range_end = models.IntegerField(null=True, blank=True, help_text="End of request range (None for infinity)")
    cost_per_1000_requests = models.DecimalField(max_digits=12, decimal_places=6)

    class Meta:
        ordering = ['range_start']

    def __str__(self):
        end = self.range_end if self.range_end else "∞"
        return f"{self.provider_model.name} Tier: {self.range_start}-{end} (${self.cost_per_1000_requests}/1k)"

class UsageLog(models.Model):
    """Every single API call is logged here for the dashboard"""
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='usage_logs')
    model = models.ForeignKey(ProviderModel, on_delete=models.SET_NULL, null=True)
    
    input_units = models.IntegerField(default=0) # Tokens or Images
    output_units = models.IntegerField(default=0)
    
    input_cost = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    output_cost = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    api_call_cost = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    
    timestamp = models.DateTimeField(auto_now_add=True)

class ProviderUsage(models.Model):
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE)
    provider_name = models.CharField(max_length=50) # e.g., 'Groq', 'GoogleVision'
    model_used = models.CharField(max_length=50)    # e.g., 'llama-3.1-70b'
    tokens_in = models.IntegerField(default=0)
    tokens_out = models.IntegerField(default=0)
    cost_estimated = models.DecimalField(max_digits=12, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']