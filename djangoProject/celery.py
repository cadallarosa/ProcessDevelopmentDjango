import os
from celery import Celery
from django.apps import apps

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')

app = Celery('djangoProject')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])

# Additional Celery Configuration
app.conf.update(
    # Timezone configuration (adjust to your timezone)
    timezone='America/Los_Angeles',
    enable_utc=True,

    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Result backend settings (if using)
    result_expires=3600,  # Results expire after 1 hour

    # Beat settings
    beat_schedule_filename='celerybeat-schedule',
)