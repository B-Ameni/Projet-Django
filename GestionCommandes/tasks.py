# app_monitoring/tasks.py

from celery import shared_task
import requests
from datetime import datetime
from .models import Metric, MetricValue, Order, AlertRule
from sklearn.ensemble import IsolationForest
import numpy as np
from django.core.mail import send_mail

PROMETHEUS_URL = "http://localhost:9090/api/v1/query"  # adapte selon ton prometheus

@shared_task
def scrape_prometheus_and_save_metrics():
    query = 'up'  # exemple, adapte à tes besoins

    response = requests.get(PROMETHEUS_URL, params={'query': query})
    if response.status_code == 200:
        data = response.json()
        results = data.get('data', {}).get('result', [])
        for result in results:
            metric_name = result['metric'].get('__name__', query)
            value_str = result['value'][1]
            timestamp = datetime.fromtimestamp(float(result['value'][0]))
            value = float(value_str)

            # Récupérer ou créer la métrique
            metric, created = Metric.objects.get_or_create(name=metric_name)
            # Créer une nouvelle valeur associée
            MetricValue.objects.create(metric=metric, value=value, timestamp=timestamp)
    else:
        print("Erreur en récupérant Prometheus", response.status_code)


@shared_task
def update_total_orders_metric():
    try:
        total = Order.objects.count()
        metric, created = Metric.objects.get_or_create(name='total_orders')
        MetricValue.objects.create(metric=metric, value=total, timestamp=datetime.now())
        return f"Métrique mise à jour: total_orders = {total}"
    except Exception as e:
        return f"Erreur lors de la mise à jour de la métrique total_orders: {str(e)}"
@shared_task
def is_anomaly(values):
    if len(values) < 2:
        return False
    mean = np.mean(values)
    std = np.std(values)
    latest = values[-1]
    z_score = (latest - mean) / std if std != 0 else 0
    return abs(z_score) > 2.5  # seuil ajustable


@shared_task
def detect_anomalies_task():
    for metric in Metric.objects.all():
        # Récupérer l'historique des valeurs
        values_qs = metric.values.order_by('timestamp').values_list('value', flat=True)
        values = list(values_qs)

        if not values:
            continue

        if is_anomaly(values):
            alert_rules = metric.alert_rules.filter(is_active=True)
            for rule in alert_rules:
                if rule.should_trigger():
                    rule.last_triggered = datetime.now()
                    rule.save()

                    # Envoyer email d'alerte
                    send_mail(
                        subject=f"Alerte: {metric.name}",
                        message=f"La valeur récente de {metric.name} a déclenché une alerte.",
                        from_email='alert@monapp.com',
                        recipient_list=[rule.notify_email],
                        fail_silently=True,
                    )
