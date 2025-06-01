from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Product, Order, Metric, OrderItem, AlertRule
from .serializers import ProductSerializer, OrderSerializer, MetricSerializer, AlertRuleSerializer
from .models import Product, Order
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import transaction
import base64
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


def home(request):
    return render(request, 'home.html')

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages

def product_list(request):
    products = Product.objects.all()
    return render(request, 'ListeProduits.html', {'products': products})

@require_POST
def add_product(request):
    name = request.POST.get('name')
    price = request.POST.get('price')
    stock = request.POST.get('stock')

    if name and price and stock:
        Product.objects.create(name=name, price=price, stock=stock)
        messages.success(request, "Produit ajouté avec succès.")
    else:
        messages.error(request, "Erreur lors de l'ajout du produit.")
    return redirect('product_list')

@require_POST
def edit_product(request):
    product_id = request.POST.get('id')
    name = request.POST.get('name')
    price = request.POST.get('price')
    product = get_object_or_404(Product, pk=product_id)
    if name and price:
        product.name = name
        product.price = price
        product.save()
        messages.success(request, "Produit modifié avec succès.")
    else:
        messages.error(request, "Erreur lors de la modification du produit.")
    return redirect('product_list')

@require_POST
def delete_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    product.delete()
    messages.success(request, "Produit supprimé avec succès.")
    return redirect('product_list')


from django.utils.dateparse import parse_datetime

def order_list(request):
    orders = Order.objects.all()
    return render(request, 'Orders.html', {'orders': orders})

@require_POST
def add_order(request):
    order_date = request.POST.get('order_date')
    dt = parse_datetime(order_date)
    if dt:
        Order.objects.create(user=request.user, order_date=dt)
        messages.success(request, "Commande ajoutée avec succès.")
    else:
        messages.error(request, "Erreur lors de l'ajout de la commande.")
    return redirect('order_list')

@require_POST
def edit_order(request):
    order_id = request.POST.get('id')
    order_date = request.POST.get('order_date')
    total_price = request.POST.get('total_price')
    order = get_object_or_404(Order, pk=order_id)
    dt = parse_datetime(order_date)
    if dt and total_price:
        order.order_date = dt
        order.total_price = total_price
        order.save()
        messages.success(request, "Commande modifiée avec succès.")
    else:
        messages.error(request, "Erreur lors de la modification de la commande.")
    return redirect('order_list')

@require_POST
def delete_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    order.delete()
    messages.success(request, "Commande supprimée avec succès.")
    return redirect('order_list')

@require_POST
def add_to_order(request, product_id):
    user = request.user
    quantity = int(request.POST.get('quantity', 0))

    product = get_object_or_404(Product, pk=product_id)

    if quantity <= 0:
        messages.error(request, "Quantité invalide.")
        return redirect('product_list')

    if quantity > product.stock:
        messages.error(request, f"Stock insuffisant pour {product.name}.")
        return redirect('product_list')

    order, created = Order.objects.get_or_create(user=user, status='En Attente')

    order_item, created_item = OrderItem.objects.get_or_create(
        order=order,
        product=product,
        defaults={'quantity': quantity}
    )

    if not created_item:
        new_quantity = order_item.quantity + quantity
        if new_quantity > product.stock:
            messages.error(request, f"Stock insuffisant pour {product.name}.")
            return redirect('product_list')
        order_item.quantity = new_quantity

    order_item.save()

    messages.success(request, f"{quantity} x {product.name} ajouté(s) à la commande.")
    return redirect('product_list')

@require_POST
def create_order_from_products(request):
    user = request.user
    products = Product.objects.all()
    items_to_order = []

    for product in products:
        qty_str = request.POST.get(f'quantity_{product.id}', '0')
        try:
            quantity = int(qty_str)
        except ValueError:
            quantity = 0

        if quantity > 0:
            if quantity > product.stock:
                messages.error(request, f"Stock insuffisant pour {product.name}.")
                return redirect('product_list')
            items_to_order.append((product, quantity))

    if not items_to_order:
        messages.error(request, "Veuillez sélectionner au moins un produit avec une quantité > 0.")
        return redirect('product_list')

    with transaction.atomic():
        order = Order.objects.create(user=user, status='En Attente')
        for product, quantity in items_to_order:
            OrderItem.objects.create(order=order, product=product, quantity=quantity)

    messages.success(request, "Commande créée avec succès.")
    return redirect('order_list')

def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if order.status == 'Livrée':
        # On ne permet pas la modification
        return redirect('order_list')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
    return redirect('order_list')  # change this to your actual view name


@require_POST
def update_order_status(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    new_status = request.POST.get('status')

    if new_status not in ['Confirmée', 'Livrée', 'Annulée', 'En attente']:
        messages.error(request, "Statut invalide.")
        return redirect('order_list')

    # Si on passe en Confirmée ou Livrée ET que ce n'était pas déjà dans ces statuts
    if new_status in ['Confirmée', 'Livrée'] and order.status not in ['Confirmée', 'Livrée']:
        # Met à jour le stock pour chaque produit de la commande
        for item in order.items.all():
            produit = item.product
            if produit.stock < item.quantity:
                messages.error(request, f"Stock insuffisant pour {produit.name}.")
                return redirect('order_list')
            produit.stock -= item.quantity
            produit.save()

    # Mets à jour le statut
    order.status = new_status
    order.save()
    messages.success(request, f"Statut de la commande {order.id} mis à jour en {new_status}.")
    return redirect('order_list')

# celery 
from .tasks import update_total_orders_metric 
from django.http import HttpResponse

def trigger_metric_update(request):
    update_total_orders_metric.delay()
    return HttpResponse("Metric update launched asynchronously")

# integrit IA
from .forecast import plot_forecast

def forecast_view(request):
    graph_html = plot_forecast()  # ou image_base64 = generate_forecast_plot(...)

    return render(request, 'forecast.html', {'graph_html': graph_html})

from .forecast import prophet_forecast

def product_forecast_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    previsions = prophet_forecast(product, days_ahead=7)

    graph_base64 = None
    if previsions:
        graph_base64 = plot_forecast(previsions, product.name)

    return render(request, 'forecast.html', {
        'product': product,
        'previsions': previsions,
        'graph_base64': graph_base64,
    })
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class MetricViewSet(viewsets.ModelViewSet):
    queryset = Metric.objects.all()
    serializer_class = MetricSerializer
 

class AlertRuleViewSet(viewsets.ModelViewSet):
    queryset = AlertRule.objects.all()
    serializer_class = AlertRuleSerializer
from prometheus_client import CollectorRegistry, Gauge, generate_latest
from django.views import View

class PrometheusMetricsView(View):
    def get(self, request, *args, **kwargs):
        # Créer un registre de métriques custom (optionnel, sinon utilise REGISTRY global)
        registry = CollectorRegistry()

        # Par exemple, définir un Gauge et l’alimenter avec une valeur extraite de ta base
        # (ici juste un exemple fictif)
        g = Gauge('my_metric_total', 'Description de ma métrique', registry=registry)
        g.set(42)  # Tu peux mettre une valeur issue de ta base, ou du queryset Metric.objects...

        # Générer la réponse au format texte Prometheus
        metrics_page = generate_latest(registry)
        return HttpResponse(metrics_page, content_type='text/plain; version=0.0.4; charset=utf-8')