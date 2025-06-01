from django.contrib import admin
from .models import Product, Order, Metric , AlertRule , MetricValue

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Metric)
admin.site.register(AlertRule)
admin.site.register(MetricValue)

# Register your models here.
