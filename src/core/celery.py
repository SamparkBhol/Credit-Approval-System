import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# 'CELERY' is a namespace, so all celery settings in settings.py
# should start with CELERY_ (e.g., CELERY_BROKER_URL)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps (i.e., from api/tasks.py)
app.autodiscover_tasks()