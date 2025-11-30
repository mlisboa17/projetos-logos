from django.urls import path
from . import views

app_name = 'verifik'

urlpatterns = [
    path('treino/', views.treino_interface, name='treino_interface'),
    path('produtos-treino/', views.produtos_lista_treino, name='produtos_lista_treino'),
    path('api/produtos/', views.api_produtos, name='api_produtos'),
    path('treinar-incremental/', views.treinar_incremental_api, name='treinar_incremental_api'),
    path('treinar-novas/', views.treinar_novas_imagens_api, name='treinar_novas_imagens'),
    path('treinar-produto/', views.treinar_produto_api, name='treinar_produto'),
]
