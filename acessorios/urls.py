from django.urls import path
from . import views

app_name = 'acessorios'

urlpatterns = [
    # Página principal
    path('', views.index_processador, name='index'),
    
    # Processamento via AJAX
    path('processar/categoria/', views.processar_categoria, name='processar_categoria'),
    path('processar/marca/', views.processar_marca, name='processar_marca'),
    path('processar/produto/', views.processar_produto, name='processar_produto'),
    path('processar/multiplos-produtos/', views.processar_multiplos_produtos, name='processar_multiplos'),
    path('processar/tudo-direto/', views.processar_tudo_direto, name='processar_tudo_direto'),
    path('processar/todas-nao-anotadas/', views.processar_todas_nao_anotadas, name='processar_todas'),
    
    # Visualização
    path('processadas/', views.listar_imagens_processadas, name='listar_processadas'),
    path('galeria/', views.galeria_processadas, name='galeria'),
]
