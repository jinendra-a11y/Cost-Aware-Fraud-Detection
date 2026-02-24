import os
import django
import shutil
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from jobs.models import Job
from analytics.models import UsageLog, ProviderUsage

def clear_test_data():
    print("🧹 Clearing test data...")
    
    # 1. Clear Database
    job_count = Job.objects.all().count()
    usage_count = UsageLog.objects.all().count()
    prov_usage_count = ProviderUsage.objects.all().count()
    Job.objects.all().delete()
    UsageLog.objects.all().delete()
    ProviderUsage.objects.all().delete()
    ProviderUsage.objects.all().delete()
    print(f"✅ Deleted {job_count} jobs, {usage_count} usage logs and {prov_usage_count } provider usage records from the database.")

    # 2. Clear Uploads
    media_uploads = Path("media/uploads")
    if media_uploads.exists():
        shutil.rmtree(media_uploads)
        media_uploads.mkdir()
        print("✅ Cleared media/uploads directory.")
    else:
        print("ℹ️ media/uploads directory does not exist.")

    print("✨ Clean slate achieved.")

if __name__ == "__main__":
    clear_test_data()
