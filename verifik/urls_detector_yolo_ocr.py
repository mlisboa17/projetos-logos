"""
URLs para Sistema YOLOv8 + OCR Django
Detector Copilot V1
"""
from django.urls import path
from . import views_detector_yolo_ocr

app_name = 'detector_yolo_ocr'

urlpatterns = [
    # Interface principal
    path('detector/yolo-ocr/', views_detector_yolo_ocr.detector_interface, name='interface'),
    
    # APIs de controle
    path('detector/yolo-ocr/iniciar/', views_detector_yolo_ocr.iniciar_deteccao, name='iniciar'),
    path('detector/yolo-ocr/parar/', views_detector_yolo_ocr.parar_deteccao, name='parar'),
    path('detector/yolo-ocr/stats/', views_detector_yolo_ocr.estatisticas_deteccao, name='stats'),
    path('detector/yolo-ocr/status/', views_detector_yolo_ocr.status_detector, name='status'),
    
    # Stream de vídeo
    path('detector/yolo-ocr/video-feed/', views_detector_yolo_ocr.video_feed, name='video_feed'),
    
    # Upload e processamento de imagem
    path('detector/yolo-ocr/upload/', views_detector_yolo_ocr.processar_imagem_upload, name='upload'),
    
    # Página de teste (debug)
    path('detector/yolo-ocr/teste/', views_detector_yolo_ocr.teste_detector, name='teste'),
]