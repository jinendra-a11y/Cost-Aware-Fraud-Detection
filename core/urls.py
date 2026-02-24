from django.urls import path
from .api import api
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls), # All routes will start with /api/jobs/...
]