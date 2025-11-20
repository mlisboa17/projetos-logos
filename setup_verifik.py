"""
Script para criar dados iniciais do VerifiK
Cria apenas estruturas que farão parte da implantação real do sistema
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from cameras.models import AIModel, Camera, CameraStatus
from accounts.models import Organization
from erp_hub.models import Store


def create_ai_models():
    """Criar modelos IA padrão (YOLOv8) que serão usados na implantação"""
    models = [
        {
            'name': 'YOLOv8 Nano',
            'version': '8.0',
            'model_file': 'yolov8n.pt',
            'model_type': 'detection',
            'classes': ['person', 'car', 'truck', 'motorcycle', 'bicycle', 'bus'],
            'accuracy': 85.5,
            'is_default': True,
            'is_active': True
        },
        {
            'name': 'YOLOv8 Small',
            'version': '8.0',
            'model_file': 'yolov8s.pt',
            'model_type': 'detection',
            'classes': ['person', 'car', 'truck', 'motorcycle', 'bicycle', 'bus', 'fire', 'smoke'],
            'accuracy': 89.2,
            'is_default': False,
            'is_active': True
        },
        {
            'name': 'YOLOv8 Medium',
            'version': '8.0',
            'model_file': 'yolov8m.pt',
            'model_type': 'detection',
            'classes': ['person', 'car', 'truck', 'motorcycle', 'bicycle', 'bus', 'fire', 'smoke', 'bottle', 'cell phone'],
            'accuracy': 92.8,
            'is_default': False,
            'is_active': True
        },
        {
            'name': 'YOLOv8 Large',
            'version': '8.0',
            'model_file': 'yolov8l.pt',
            'model_type': 'detection',
            'classes': ['person', 'car', 'truck', 'motorcycle', 'bicycle', 'bus', 'fire', 'smoke', 'bottle', 'cell phone', 'knife', 'backpack'],
            'accuracy': 94.5,
            'is_default': False,
            'is_active': True
        },
        {
            'name': 'YOLOv8 Segmentation',
            'version': '8.0',
            'model_file': 'yolov8n-seg.pt',
            'model_type': 'segmentation',
            'classes': ['person', 'car', 'fire', 'smoke'],
            'accuracy': 87.3,
            'is_default': False,
            'is_active': True
        }
    ]
    
    for model_data in models:
        model, created = AIModel.objects.get_or_create(
            name=model_data['name'],
            version=model_data['version'],
            defaults=model_data
        )
        
        if created:
            print(f"✅ Modelo IA criado: {model.name} v{model.version} ({model.accuracy}% acurácia)")
        else:
            print(f"ℹ️  Modelo IA já existe: {model.name} v{model.version}")


def show_deployment_info():
    """Mostra informações sobre a implantação"""
    print("\n" + "="*60)
    print("📋 INFORMAÇÕES PARA IMPLANTAÇÃO DO VERIFIK")
    print("="*60)
    
    print("\n🎯 MODELOS IA DISPONÍVEIS:")
    models = AIModel.objects.filter(is_active=True)
    for model in models:
        default = " [PADRÃO]" if model.is_default else ""
        print(f"   • {model.name} v{model.version}{default}")
        print(f"     Tipo: {model.get_model_type_display()}")
        print(f"     Arquivo: {model.model_file}")
        print(f"     Acurácia: {model.accuracy}%")
        print(f"     Classes: {len(model.classes)} objetos detectáveis")
        print()
    
    print("\n📹 CONFIGURAÇÃO DE CÂMERAS:")
    print("   Para adicionar câmeras:")
    print("   1. Acesse: /admin/cameras/camera/")
    print("   2. Clique em 'Adicionar câmera'")
    print("   3. Preencha:")
    print("      - Organização: Grupo Lisboa")
    print("      - Loja: Selecione a unidade")
    print("      - Nome: Ex: 'Câmera Caixa 1'")
    print("      - Código: Ex: 'CAM-CX1'")
    print("      - Localização: Ex: 'Caixa 1'")
    print("      - Stream URL: rtsp://usuario:senha@ip:porta/stream")
    print("      - Modelo IA: YOLOv8 Nano (padrão)")
    print("      - Threshold: 0.6 (recomendado)")
    print("      - Classes: ['person', 'car', 'truck']")
    
    print("\n🔔 TIPOS DE EVENTOS DETECTÁVEIS:")
    from cameras.models import EventType
    for choice in EventType.choices:
        print(f"   • {choice[1]}")
    
    print("\n⚙️ CONFIGURAÇÃO RECOMENDADA POR LOCALIZAÇÃO:")
    print("\n   CAIXAS E PDV:")
    print("   - Detecção: person, backpack, cell phone")
    print("   - Eventos: queue (filas), theft (possível furto)")
    print("   - FPS: 5 frames/segundo")
    
    print("\n   PISTAS DE ABASTECIMENTO:")
    print("   - Detecção: person, car, truck, fire, smoke")
    print("   - Eventos: spillage, wrong_way, abandoned_vehicle")
    print("   - FPS: 3 frames/segundo")
    
    print("\n   ENTRADA/ESTACIONAMENTO:")
    print("   - Detecção: person, car, motorcycle")
    print("   - Eventos: loitering, crowd, parking_violation")
    print("   - FPS: 2 frames/segundo")
    
    print("\n   ESTOQUE:")
    print("   - Detecção: person, fire, smoke")
    print("   - Eventos: intrusion, fire, shelf_empty")
    print("   - FPS: 1 frame/segundo")
    
    print("\n📊 APIs DISPONÍVEIS:")
    print("   • GET  /api/cameras/           - Listar câmeras")
    print("   • GET  /api/cameras/stats/     - Estatísticas")
    print("   • POST /api/cameras/{id}/start_recording/")
    print("   • POST /api/cameras/{id}/enable_ai/")
    print("   • GET  /api/events/            - Listar eventos")
    print("   • GET  /api/events/unacknowledged/ - Eventos pendentes")
    print("   • POST /api/events/{id}/acknowledge/")
    print("   • GET  /api/alerts/unread/     - Alertas não lidos")
    
    print("\n💾 ARMAZENAMENTO:")
    print("   - Retenção padrão: 30 dias")
    print("   - Snapshots: /media/cameras/snapshots/")
    print("   - Vídeos: /media/cameras/videos/")
    
    print("\n🔐 PERMISSÕES:")
    print("   • Super Admin: Acesso total")
    print("   • Org Admin: Câmeras da organização")
    print("   • Usuário: Apenas visualização")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    print("🎥 Iniciando setup do VerifiK...\n")
    
    print("1️⃣ Criando modelos IA YOLOv8...")
    create_ai_models()
    
    print("\n🎉 Setup do VerifiK completo!")
    
    show_deployment_info()
    
    print("\n✅ Sistema pronto para implantação!")
    print("   Próximo passo: Adicionar câmeras no Django Admin")

