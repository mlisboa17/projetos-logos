"""
URLs do módulo VerifiK API
"""
from django.urls import path
from . import api_deteccao

urlpatterns = [
    # API de Detecção
    path('detectar/', api_deteccao.detectar_produtos, name='api_detectar_produtos'),
    path('detectar/teste/', api_deteccao.detectar_teste, name='api_detectar_teste'),
]
