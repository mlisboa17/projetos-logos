"""
Script para cadastrar a câmera Intelbras no sistema VerifiK
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import Camera
from accounts.models import Organization

# Buscar organização (Grupo Lisboa)
org = Organization.objects.first()

if not org:
    print("❌ Nenhuma organização encontrada")
    print("   Execute: python setup_initial_data.py")
    exit(1)

print(f"🏢 Organização: {org.name}")

# Dados da câmera Intelbras
CAMERA_DATA = {
    'nome': 'Câmera Intelbras Caixa 1',
    'localizacao': 'Caixa Principal',
    'ip_address': '192.168.68.110',
    'porta': 554,
    'usuario': 'E6803',
    'senha': 'C@sa3863',  # Primeira senha para testar
}

# URLs RTSP possíveis para Intelbras
urls_testar = [
    f"rtsp://{CAMERA_DATA['usuario']}:{CAMERA_DATA['senha']}@{CAMERA_DATA['ip_address']}:554/cam/realmonitor?channel=1&subtype=0",
    f"rtsp://{CAMERA_DATA['usuario']}:{CAMERA_DATA['senha']}@{CAMERA_DATA['ip_address']}:554/cam/realmonitor?channel=1&subtype=1",
    f"rtsp://{CAMERA_DATA['usuario']}:{CAMERA_DATA['senha']}@{CAMERA_DATA['ip_address']}:554/",
]

print(f"\n{'='*70}")
print("📸 CADASTRANDO CÂMERA INTELBRAS")
print(f"{'='*70}")
print(f"Nome: {CAMERA_DATA['nome']}")
print(f"IP: {CAMERA_DATA['ip_address']}:{CAMERA_DATA['porta']}")
print(f"Usuário: {CAMERA_DATA['usuario']}")
print(f"Organização: {org.name}")

# Verificar se já existe
camera_existente = Camera.objects.filter(
    ip_address=CAMERA_DATA['ip_address']
).first()

if camera_existente:
    print(f"\n⚠️ Câmera já cadastrada: {camera_existente.nome}")
    print(f"   ID: {camera_existente.id}")
    print(f"   Status: {camera_existente.get_status_display()}")
    
    atualizar = input("\nAtualizar dados? (s/n): ").lower()
    if atualizar == 's':
        camera_existente.nome = CAMERA_DATA['nome']
        camera_existente.localizacao = CAMERA_DATA['localizacao']
        camera_existente.usuario = CAMERA_DATA['usuario']
        camera_existente.senha = CAMERA_DATA['senha']
        camera_existente.url_stream = urls_testar[0]
        camera_existente.save()
        print("✅ Câmera atualizada!")
        camera = camera_existente
    else:
        camera = camera_existente
else:
    # Criar nova câmera
    camera = Camera.objects.create(
        organization=org,
        nome=CAMERA_DATA['nome'],
        localizacao=CAMERA_DATA['localizacao'],
        ip_address=CAMERA_DATA['ip_address'],
        porta=CAMERA_DATA['porta'],
        usuario=CAMERA_DATA['usuario'],
        senha=CAMERA_DATA['senha'],
        url_stream=urls_testar[0],
        status='ATIVA',
        ativa=True,
        resolucao='1920x1080',
        fps=30
    )
    print(f"\n✅ Câmera cadastrada com sucesso!")
    print(f"   ID: {camera.id}")

print(f"\n{'='*70}")
print("📋 DADOS DA CÂMERA")
print(f"{'='*70}")
print(f"ID: {camera.id}")
print(f"Nome: {camera.nome}")
print(f"Local: {camera.localizacao}")
print(f"IP: {camera.ip_address}:{camera.porta}")
print(f"Status: {camera.get_status_display()}")
print(f"URL Stream: {camera.url_stream}")
print(f"\n{'='*70}")

print("\n🎯 PRÓXIMOS PASSOS:")
print("1. Testar conexão:")
print(f"   python conectar_camera_verifik.py")
print("   Escolha opção 2 (Testar conexão)")
print("\n2. Ver vídeo ao vivo:")
print(f"   python conectar_camera_verifik.py")
print("   Escolha opção 3 (Ver vídeo)")
print("\n3. Detectar produtos:")
print(f"   python exemplo_deteccao_camera.py")
