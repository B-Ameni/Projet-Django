# GestionCommandes/schema.py
import graphene
from graphene_django.types import DjangoObjectType
from GestionCommandes.models import Product, Order, OrderItem
from django.contrib.auth.models import User

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"

class OrderItemType(DjangoObjectType):
    class Meta:
        model = OrderItem
        fields = "__all__"

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"

    total_price = graphene.Float()

    def resolve_total_price(parent, info):
        return parent.total_price()

class Query(graphene.ObjectType):
    all_products = graphene.List(ProductType)
    all_orders = graphene.List(OrderType)
    order_by_id = graphene.Field(OrderType, id=graphene.Int())

    def resolve_all_products(root, info):
        return Product.objects.all()

    def resolve_all_orders(root, info):
        return Order.objects.prefetch_related("items__product").all()

    def resolve_order_by_id(root, info, id):
        return Order.objects.get(pk=id)
class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=True)

    product = graphene.Field(ProductType)

    def mutate(self, info, name, price, stock):
        product = Product(name=name, price=price, stock=stock)
        product.save()
        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):
    order = graphene.Field(OrderType)

    class Arguments:
        status = graphene.String(required=False, default_value="En attente")

    def mutate(self, info, status):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Authentification requise")
        order = Order.objects.create(user=user, status=status)
        return CreateOrder(order=order)
class AddOrderItem(graphene.Mutation):
    order_item = graphene.Field(OrderItemType)

    class Arguments:
        order_id = graphene.Int(required=True)
        product_id = graphene.Int(required=True)
        quantity = graphene.Int(required=True)

    def mutate(self, info, order_id, product_id, quantity):
        try:
            order = Order.objects.get(id=order_id)
            product = Product.objects.get(id=product_id)
        except (Order.DoesNotExist, Product.DoesNotExist):
            raise Exception("Commande ou produit introuvable")

        if product.stock < quantity:
            raise Exception("Stock insuffisant")

        # Si l'item existe déjà dans la commande, on le met à jour
        order_item, created = OrderItem.objects.get_or_create(
            order=order, product=product,
            defaults={"quantity": quantity}
        )
        if not created:
            order_item.quantity += quantity
        order_item.full_clean()
        order_item.save()

        return AddOrderItem(order_item=order_item)
    
class Mutation(graphene.ObjectType):
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    add_order_item = AddOrderItem.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
class ProductType(DjangoObjectType):
    class Meta:
        model = Product

class Query(graphene.ObjectType):
    products_by_min_stock = graphene.List(ProductType, min_stock=graphene.Int(required=True))

    def resolve_products_by_min_stock(root, info, min_stock):
        return Product.objects.filter(stock__gt=min_stock)
class Query(graphene.ObjectType):
    product_search = graphene.List(ProductType, name_contains=graphene.String(required=True))

    def resolve_product_search(root, info, name_contains):
        return Product.objects.filter(name__icontains=name_contains)

class OrderType(DjangoObjectType):
    class Meta:
        model = Order

class Query(graphene.ObjectType):
    orders_by_user = graphene.List(OrderType, user_id=graphene.Int(required=True))

    def resolve_orders_by_user(root, info, user_id):
        return Order.objects.filter(user__id=user_id)
# Combine all queries into a single Query class to avoid conflicts

class Query(graphene.ObjectType):
    all_products = graphene.List(ProductType)
    all_orders = graphene.List(OrderType)
    order_by_id = graphene.Field(OrderType, id=graphene.Int())
    products_by_min_stock = graphene.List(ProductType, min_stock=graphene.Int(required=True))
    product_search = graphene.List(ProductType, name_contains=graphene.String(required=True))
    orders_by_user = graphene.List(OrderType, user_id=graphene.Int(required=True))

    def resolve_all_products(root, info):
        return Product.objects.all()

    def resolve_all_orders(root, info):
        return Order.objects.prefetch_related("items__product").all()

    def resolve_order_by_id(root, info, id):
        return Order.objects.get(pk=id)

    def resolve_products_by_min_stock(root, info, min_stock):
        return Product.objects.filter(stock__gt=min_stock)

    def resolve_product_search(root, info, name_contains):
        return Product.objects.filter(name__icontains=name_contains)

    def resolve_orders_by_user(root, info, user_id):
        return Order.objects.filter(user__id=user_id)


schema = graphene.Schema(query=Query, mutation=Mutation)





