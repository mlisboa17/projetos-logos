from django.urls import path
from . import views

app_name = 'cameras'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('camera/<int:camera_id>/', views.camera_detail, name='camera_detail'),
    path('events/', views.events_list, name='events_list'),
]
