"""
URLs da aplicação fuel_prices
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_consolidado, name='dashboard_consolidado'),  # Dashboard combustíveis
    path('por-produto/', views.dashboard_vibra, name='dashboard_vibra'),
    path('por-posto/', views.dashboard_por_posto, name='dashboard_por_posto'),
    path('executar-scraper/', views.executar_scraper, name='executar_scraper'),
    path('api/precos-por-data/', views.api_precos_por_data, name='api_precos_por_data'),  # API histórico
]
