from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('En attente', 'En attente'),
        ('Confirmée', 'Confirmée'),
        ('Livrée', 'Livrée'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='En attente')
    order_date = models.DateTimeField(auto_now_add=True)
    #delivery_date = models.DateField(null=True, blank=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Commande {self.id} - {self.user.username}"

    def total_price(self):
        return sum(item.subtotal() for item in self.items.all())
        

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def subtotal(self):
        return self.quantity * self.product.price

    def clean(self):
        # Vérifie que la quantité commandée est disponible en stock
        if self.quantity > self.product.stock:
            raise ValidationError(f"Stock insuffisant pour le produit : {self.product.name}")


from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class Metric(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
class MetricValue(models.Model):
    metric = models.ForeignKey(Metric, on_delete=models.CASCADE, related_name='values')
    value = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.metric.name} = {self.value} @ {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
class AlertRule(models.Model):
    COMPARISON_CHOICES = [
        ('>', 'Greater than'),
        ('<', 'Less than'),
        ('>=', 'Greater or equal'),
        ('<=', 'Less or equal'),
        ('==', 'Equal'),
        ('!=', 'Not equal'),
    ]

    metric = models.ForeignKey(Metric, on_delete=models.CASCADE, related_name='alert_rules')
    threshold = models.FloatField()
    condition = models.CharField(max_length=2, choices=COMPARISON_CHOICES)
    notify_email = models.EmailField()
    is_active = models.BooleanField(default=True)
    last_triggered = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('metric', 'threshold', 'condition')

    def clean(self):
        if self.threshold < 0:
            raise ValidationError("Le seuil doit être positif.")
        if self.condition not in dict(self.COMPARISON_CHOICES):
            raise ValidationError("Condition de comparaison invalide.")

    def __str__(self):
        return f"Alerte: {self.metric.name} {self.condition} {self.threshold}"

    def should_trigger(self):
        # Évalue si l'alerte est déclenchée
        value = self.metric.value
        cond = self.condition
        threshold = self.threshold

        return eval(f"{value} {cond} {threshold}")
