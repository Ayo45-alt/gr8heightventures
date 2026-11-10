from django.urls import path

from . import views


urlpatterns = [
    path('', views.owner_dashboard, name='owner-dashboard'),
    path('login/', views.owner_login, name='owner-login'),
    path('logout/', views.owner_logout, name='owner-logout'),
    path('products/add/', views.add_product, name='owner-product-add'),
    path('products/<int:product_id>/edit/', views.edit_product, name='owner-product-edit'),
    path('orders/<int:order_id>/status/', views.update_order_status, name='owner-order-status'),
]
