from django.urls import path
from . import views

app_name = 'transcricao_caixa'

urlpatterns = [
    # Página inicial
    path('', views.index, name='index'),
    
    # Fechamentos de Caixa
    path('fechamentos/', views.lista_fechamentos, name='lista_fechamentos'),
    path('fechamentos/novo/', views.novo_fechamento, name='novo_fechamento'),
    path('fechamentos/<int:pk>/', views.detalhe_fechamento, name='detalhe_fechamento'),
    path('fechamentos/<int:pk>/editar/', views.editar_fechamento, name='editar_fechamento'),
    
    # Upload e Processamento de Documentos
    path('fechamentos/<int:fechamento_id>/upload/', views.upload_documento, name='upload_documento'),
    path('documentos/<int:pk>/processar/', views.processar_documento, name='processar_documento'),
    path('documentos/<int:pk>/revisar/', views.revisar_documento, name='revisar_documento'),
    path('documentos/<int:pk>/editar/', views.editar_documento, name='editar_documento'),
    
    # APIs
    path('api/processar-lote/', views.processar_lote, name='processar_lote'),
    path('api/documentos/<int:pk>/dados/', views.obter_dados_documento, name='obter_dados_documento'),
]
