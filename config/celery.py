"""
Celery application configuration.

This module ensures Celery picks up Django settings and provides a ready-to-use
Celery app instance that can be imported across the codebase.
"""
import os

from celery import Celery

# Default Django settings module for Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("sademiy-api")

# Load Celery settings from Django settings using the CELERY namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks across installed apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Simple Celery task for debugging worker configuration."""
    print(f"Request: {self.request!r}")

