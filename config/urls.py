"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.contrib import admin
from django.urls import path
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from GestionCommandes import views
from django.contrib.auth import views as auth_views
from GestionCommandes.views import home, trigger_metric_update, forecast_view, MetricViewSet , AlertRuleViewSet
from graphene_django.views import GraphQLView
from GestionCommandes.schema import schema
from GestionCommandes.views import PrometheusMetricsView
router = DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'orders', views.OrderViewSet)
router.register(r'metrics', MetricViewSet ,  basename='metric')
router.register(r'alerts', AlertRuleViewSet , basename='alert')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    #path('api-auth/', include('rest_framework.urls')),
    path('api/products/', views.product_list, name='product-list'),
    path('api/orders/', views.order_list, name='order-list'),
   #path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    #path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('accueil/', home, name='home'),
    path('produits/', views.product_list, name='product_list'),
    path('produits/add/', views.add_product, name='add_product'),
    path('produits/edit/', views.edit_product, name='edit_product'),
    path('produits/delete/<int:product_id>/', views.delete_product, name='delete_product'),

    path('orders/', views.order_list, name='order_list'),
    path('orders/add/', views.add_order, name='add_order'),
    path('orders/edit/', views.edit_order, name='edit_order'),
    path('orders/delete/<int:order_id>/', views.delete_order, name='delete_order'),
    path('produits/<int:product_id>/add_to_order/', views.add_to_order, name='add_to_order'),
    path('produits/create_order/', views.create_order_from_products, name='create_order_from_products'),
    path('orders/<int:order_id>/update_status/', views.update_order_status, name='update_order_status'),
   # path('orders/<int:order_id>/update_status/', views.update_order_status, name='update_order_status'),
    path("graphql/", GraphQLView.as_view(graphiql=True, schema=schema)),
    path('trigger-metric/', trigger_metric_update, name='celery'),
    path('forecast/<int:product_id>/', views.product_forecast_view, name='previsions'),
 #path('monitoring/metrics/', MetricViewSet.as_view(), name='metrics_list'),
    #path('monitoring/alerts/', AlertRuleViewSet.as_view(), name='alerts_list'),]
     path('monitoring/', include(router.urls)),
     path('metrics/', PrometheusMetricsView.as_view(), name='prometheus-metrics'),
]
