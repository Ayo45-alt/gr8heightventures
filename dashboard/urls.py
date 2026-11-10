from django.urls import path

from . import views


urlpatterns = [
    path('', views.owner_dashboard, name='owner-dashboard'),
    path('login/', views.owner_login, name='owner-login'),
    path('logout/', views.owner_logout, name='owner-logout'),
]
