# URLs para o sistema de coleta de imagens
from django.urls import path
from .views_coleta import (
    enviar_fotos,
    revisar_fotos,
    aprovar_imagem,
    rejeitar_imagem,
    listar_lotes,
    detalhe_lote,
    aprovar_lote_completo,
    aprovar_produto_lote,
    detectar_produtos_api,
    revisar_desconhecidos,
    reclassificar_imagem,
    aprovar_bbox_api,
    processar_automatico,
    processar_automatico_api,
    aprovar_processamento,
)

urlpatterns = [
    path('enviar-fotos/', enviar_fotos, name='enviar_fotos'),
    path('revisar-fotos/', revisar_fotos, name='revisar_fotos'),
    path('aprovar-imagem/<int:imagem_id>/', aprovar_imagem, name='aprovar_imagem'),
    path('rejeitar-imagem/<int:imagem_id>/', rejeitar_imagem, name='rejeitar_imagem'),
    path('lotes/', listar_lotes, name='listar_lotes'),
    path('lote/<int:lote_id>/', detalhe_lote, name='detalhe_lote'),
    path('lote/<int:lote_id>/aprovar-tudo/', aprovar_lote_completo, name='aprovar_lote_completo'),
    path('lote/<int:lote_id>/aprovar-produto/<int:produto_id>/', aprovar_produto_lote, name='aprovar_produto_lote'),
    path('api/detectar-produtos/', detectar_produtos_api, name='detectar_produtos_api'),
    path('api/aprovar-bbox/', aprovar_bbox_api, name='aprovar_bbox_api'),
    path('processar-automatico/', processar_automatico, name='processar_automatico'),
    path('api/processar-automatico/', processar_automatico_api, name='processar_automatico_api'),
    path('api/aprovar-processamento/', aprovar_processamento, name='aprovar_processamento'),
    path('revisar-desconhecidos/', revisar_desconhecidos, name='revisar_desconhecidos'),
    path('reclassificar/<int:imagem_id>/', reclassificar_imagem, name='reclassificar_imagem'),
]
