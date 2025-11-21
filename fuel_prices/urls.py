"""
URLs da aplicação fuel_prices
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_vibra, name='dashboard_vibra'),
    path('por-posto/', views.dashboard_por_posto, name='dashboard_por_posto'),
]
