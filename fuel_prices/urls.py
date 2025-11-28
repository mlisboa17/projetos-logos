"""
URLs da aplicação fuel_prices
"""
from django.urls import path
from . import views
from . import api_scraper

urlpatterns = [
    path('', views.dashboard_consolidado, name='dashboard_consolidado'),  # Dashboard combustíveis
    path('por-produto/', views.dashboard_vibra, name='dashboard_vibra'),
    path('por-posto/', views.dashboard_por_posto, name='dashboard_por_posto'),
    path('executar-scraper/', views.executar_scraper, name='executar_scraper'),
    path('api/precos-por-data/', views.api_precos_por_data, name='api_precos_por_data'),  # API histórico
    
    # APIs para scraper standalone
    path('api/scraper-data/', api_scraper.receber_dados_scraper, name='api_scraper_data'),
    path('api/status/', api_scraper.status_sistema, name='api_status'),
    
    # APIs para sistema Logus/Price
    path('api/logus-feed/', views.api_logus_feed, name='api_logus_feed'),
    path('api/precos-atual/', views.api_precos_atual, name='api_precos_atual'),
    path('api/resumo-postos/', views.api_resumo_postos, name='api_resumo_postos'),
]
