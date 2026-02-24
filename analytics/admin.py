from django.contrib import admin
from .models import ProviderModel, UsageLog, ProviderUsage, PricingTier

class PricingTierInline(admin.TabularInline):
    model = PricingTier
    extra = 1

@admin.register(ProviderModel)
class ProviderModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_identifier', 'provider_type', 'input_cost_per_million', 'output_cost_per_million')
    inlines = [PricingTierInline]

@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ('job', 'model', 'total_cost', 'timestamp')
    readonly_fields = ('timestamp',)

admin.site.register(ProviderUsage)
