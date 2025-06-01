# monprojet/celery.py

import os
from celery import Celery
from celery.schedules import crontab
from celery import shared_task
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

app.config_from_object('django.conf:settings', namespace='CELERY')

# IMPORTANT : autodiscover tous les modules contenant des tâches
#app.autodiscover_tasks(['GestionCommandes'])
app.autodiscover_tasks()
app.conf.beat_schedule = {
    'scrape-prometheus-every-5-minutes': {
        'task': 'GestionCommandes.tasks.scrape_prometheus_and_save_metrics',
        'schedule': crontab(minute='*/5'),  # toutes les 5 minutes
    },
}

app.conf.beat_schedule = {
    'update-total-orders-every-5-minutes': {
        'task': 'GestionCommandes.tasks.update_total_orders_metric',
        'schedule': crontab(minute='*/5'),  # toutes les 5 minutes
    },
}
