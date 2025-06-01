import pandas as pd
from prophet import Prophet
import datetime
from django.utils import timezone
from django.db import models
from .models import OrderItem

def prophet_forecast(product, days_ahead=7):
    today = timezone.now().date()
    start_date = today - datetime.timedelta(days=90)  # 3 mois de données passées

    # Récupérer les ventes du produit dans les commandes livrées sur cette période
    qs = OrderItem.objects.filter(
        product=product,
        order__order_date__date__gte=start_date,
        order__order_date__date__lt=today,
        order__status='Livrée',
    ).values('order__order_date__date').annotate(total_qty=models.Sum('quantity'))

    # Construire le DataFrame attendu par Prophet
    data = [{'ds': r['order__order_date__date'], 'y': r['total_qty']} for r in qs]
    df = pd.DataFrame(data)

    # Si pas assez de données, retourne vide
    if df.empty or len(df) < 10:
        return None

    # Remplir les dates manquantes avec 0 (important pour Prophet)
    df = df.set_index('ds').asfreq('D').fillna(0).reset_index()

    # Modèle Prophet
    model = Prophet()
    model.fit(df)

    # Prévision
    future = model.make_future_dataframe(periods=days_ahead)
    forecast = model.predict(future)

    # On ne garde que les dates futures
    forecast_future = forecast[forecast['ds'] > pd.Timestamp(today)][['ds', 'yhat']]

    # Retourne une liste de tuples (date, prediction arrondie)
    return [(row['ds'].date(), max(0, round(row['yhat']))) for _, row in forecast_future.iterrows()]

import matplotlib.pyplot as plt
import io
import base64

def plot_forecast(previsions, product_name):
    """
    previsions : liste de tuples (date, quantité prévue)
    Retourne une chaîne base64 représentant l’image PNG.
    """
    dates = [p[0] for p in previsions]
    qtys = [p[1] for p in previsions]

    plt.figure(figsize=(8, 4))
    plt.plot(dates, qtys, marker='o', linestyle='-')
    plt.title(f"Prévision des commandes pour {product_name}")
    plt.xlabel("Date")
    plt.ylabel("Quantité prévue")
    plt.grid(True)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return image_base64
