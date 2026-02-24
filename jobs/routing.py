from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # ws://localhost:8000/ws/job/<job_id>/
    re_path(r'ws/job/(?P<job_id>\w+)/$', consumers.JobStatusConsumer.as_asgi()),
]