from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views_visualizacao import visualizar_anotacoes
from django.views.static import serve
from django.conf import settings
from pathlib import Path

router = DefaultRouter()
router.register(r'funcionarios', views.FuncionarioViewSet)
router.register(r'perfis-gestor', views.PerfilGestorViewSet)
router.register(r'produtos', views.ProdutoMaeViewSet)
router.register(r'vendas', views.OperacaoVendaViewSet)
router.register(r'itens-venda', views.ItemVendaViewSet)
router.register(r'deteccoes', views.DeteccaoProdutoViewSet)
router.register(r'incidentes', views.IncidenteViewSet)
router.register(r'evidencias', views.EvidenciaIncidenteViewSet)
router.register(r'alertas', views.AlertaViewSet)
router.register(r'cameras', views.CameraViewSet)
router.register(r'camera-status', views.CameraStatusViewSet)

urlpatterns = [
    # Páginas HTML
    path('', views.home, name='verifik_home'),
    path('produtos/', views.produtos_lista, name='verifik_produtos_lista'),
    path('produtos/novo/', views.produto_criar, name='verifik_produto_criar'),
    path('produtos/<int:pk>/', views.produto_detalhe, name='verifik_produto_detalhe'),
    path('produtos/<int:pk>/editar/', views.produto_editar, name='verifik_produto_editar'),
    path('produtos/<int:produto_id>/adicionar-imagem/', views.adicionar_imagem, name='verifik_adicionar_imagem'),
    path('imagens/<int:imagem_id>/remover/', views.remover_imagem, name='verifik_remover_imagem'),
    
    # Visualizar imagens anotadas
    path('imagens-anotadas/', views.listar_imagens_anotadas, name='verifik_imagens_anotadas'),
    path('imagens-anotadas/<int:img_id>/', views.visualizar_imagem_anotada, name='verifik_visualizar_anotada'),
    
    # API REST
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    
    # Sistema de coleta de imagens
    path('coleta/', include('verifik.urls_coleta')),
    path('coleta/', include('verifik.urls_anotacao')),
    path('coleta/', include('verifik.urls_importacao')),
    
    # Visualização de anotações
    path('visualizar-anotacoes/', visualizar_anotacoes, name='visualizar_anotacoes'),
    
    # Interface de Detecção Inteligente
    path('deteccao-inteligente/', views.deteccao_inteligente, name='verifik_deteccao_inteligente'),
    path('api/detectar-imagem/', views.api_detectar_imagem, name='verifik_api_detectar_imagem'),
]
