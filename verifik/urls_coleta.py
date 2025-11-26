# URLs para o sistema de coleta de imagens
from django.urls import path
from .views_coleta import (
    enviar_fotos,
    revisar_fotos,
    aprovar_imagem,
    rejeitar_imagem,
)

urlpatterns = [
    path('enviar-fotos/', enviar_fotos, name='enviar_fotos'),
    path('revisar-fotos/', revisar_fotos, name='revisar_fotos'),
    path('aprovar-imagem/<int:imagem_id>/', aprovar_imagem, name='aprovar_imagem'),
    path('rejeitar-imagem/<int:imagem_id>/', rejeitar_imagem, name='rejeitar_imagem'),
]
