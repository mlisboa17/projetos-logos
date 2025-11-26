from django.urls import path
from . import views

app_name = 'solar_monitor'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('usina/<int:usina_id>/', views.usina_detalhes, name='usina_detalhes'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('alertas/', views.alertas, name='alertas'),
    
    # APIs JSON
    path('api/usina/<int:usina_id>/realtime/', views.api_leituras_realtime, name='api_realtime'),
    path('api/status-geral/', views.api_status_geral, name='api_status_geral'),
]
