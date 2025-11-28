# URLs para importação de pastas standalone

from django.urls import path
from .views_importacao import (
    importar_pasta_standalone,
    executar_importacao_pasta,
)

urlpatterns = [
    path('importar-pasta/', importar_pasta_standalone, name='importar_pasta_standalone'),
    path('importar-pasta/executar/', executar_importacao_pasta, name='executar_importacao_pasta'),
]