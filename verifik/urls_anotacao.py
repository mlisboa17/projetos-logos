# URLs para o sistema de anotação de imagens

from django.urls import path
from .views_anotacao import (
    anotar_imagem,
    editar_anotacoes,
    salvar_anotacao,
    remover_anotacao,
    finalizar_anotacao,
    importar_dataset,
    executar_importacao,
    exportar_dataset,
)

urlpatterns = [
    path('anotar/', anotar_imagem, name='anotar_imagem'),
    path('anotar/<int:imagem_id>/editar/', editar_anotacoes, name='editar_anotacoes'),
    path('anotar/salvar/', salvar_anotacao, name='salvar_anotacao'),
    path('anotar/remover/<int:anotacao_id>/', remover_anotacao, name='remover_anotacao'),
    path('anotar/<int:imagem_id>/finalizar/', finalizar_anotacao, name='finalizar_anotacao'),
    path('importar-dataset/', importar_dataset, name='importar_dataset'),
    path('importar-dataset/executar/', executar_importacao, name='executar_importacao'),
    path('exportar-dataset/', exportar_dataset, name='exportar_dataset'),
]
