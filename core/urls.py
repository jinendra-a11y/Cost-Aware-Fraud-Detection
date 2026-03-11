from django.urls import path
from django.http import JsonResponse
from .api import api
from django.contrib import admin


def root(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "cost-aware-fraud-detection",
        }
    )


def healthz(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("", root),
    path("healthz", healthz),
    path('admin/', admin.site.urls),
    path('api/', api.urls), # All routes will start with /api/jobs/...
]