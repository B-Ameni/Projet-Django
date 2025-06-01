from rest_framework import serializers
from .models import Metric, Product, Order, OrderItem, AlertRule
# GestionCommandes/serializers.py
from rest_framework import serializers
from .models import Product, Order, OrderItem

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['product', 'product_name', 'quantity', 'subtotal']

    def get_subtotal(self, obj):
        return obj.subtotal()
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'status', 'order_date', 'last_modified', 'user', 'items', 'total_price']

    def get_total_price(self, obj):
        return obj.total_price()
class MetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metric
        fields = '__all__'

class AlertRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertRule
        fields = '__all__'

    def validate_threshold(self, value):
        if value < 0:
            raise serializers.ValidationError("Le seuil doit être positif.")
        return value