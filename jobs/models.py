from django.db import models
import uuid

class Job(models.Model):
    STATUS_CHOICES = [
        ('QUEUED', 'Queued'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    job_id = models.CharField(max_length=100, unique=True) # From your current input
    pickup_location = models.CharField(max_length=255)
    drop_location = models.CharField(max_length=255)
    pickup_time = models.DateTimeField()
    drop_time = models.DateTimeField()
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='QUEUED')
    progress = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Store the final JSON result here instead of just Redis
    final_result = models.JSONField(null=True, blank=True)
    
    # Store intermediate normalized bills for auditing
    normalized_bills = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Job {self.job_id} - {self.status}"