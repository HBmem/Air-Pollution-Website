# air_pollution_website/celery.py

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "air_pollution_website.settings")
app = Celery("air_pollution_website")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()