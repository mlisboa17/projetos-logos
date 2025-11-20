from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'funcionarios', views.FuncionarioViewSet)
router.register(r'perfis-gestor', views.PerfilGestorViewSet)
router.register(r'produtos', views.ProdutoViewSet)
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
    path('produtos/<int:pk>/', views.produto_detalhe, name='verifik_produto_detalhe'),
    path('produtos/<int:produto_id>/adicionar-imagem/', views.adicionar_imagem, name='verifik_adicionar_imagem'),
    path('imagens/<int:imagem_id>/remover/', views.remover_imagem, name='verifik_remover_imagem'),
    
    # API REST
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]
