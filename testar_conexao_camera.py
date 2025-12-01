"""
Script direto para testar conexão com a câmera Intelbras
"""
import os
import django
import cv2
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import Camera, CameraStatus

print("="*70)
print("🎥 TESTE DE CONEXÃO - CÂMERA INTELBRAS")
print("="*70)

# Buscar câmera
camera = Camera.objects.first()

if not camera:
    print("❌ Nenhuma câmera cadastrada")
    exit(1)

print(f"\n📸 Câmera: {camera.nome}")
print(f"   Local: {camera.localizacao}")
print(f"   IP: {camera.ip_address}:{camera.porta}")
print(f"   URL: {camera.url_stream}")
print(f"\n⏳ Conectando...")

try:
    inicio = datetime.now()
    
    # Tentar conectar
    cap = cv2.VideoCapture(camera.url_stream)
    
    if not cap.isOpened():
        print("\n❌ NÃO FOI POSSÍVEL CONECTAR")
        print("\nPossíveis causas:")
        print("  1. Câmera desligada")
        print("  2. Computador não está na mesma rede (192.168.68.x)")
        print("  3. Credenciais incorretas")
        print("  4. URL RTSP incorreta")
        
        # Registrar erro
        CameraStatus.objects.create(
            camera=camera,
            status='ERRO_CONEXAO',
            mensagem_erro='Não foi possível abrir a conexão'
        )
        
        exit(1)
    
    print("✅ Conexão estabelecida!")
    
    # Tentar ler frame
    ret, frame = cap.read()
    
    fim = datetime.now()
    latencia = (fim - inicio).total_seconds() * 1000
    
    if not ret or frame is None:
        print("\n⚠️ Conexão aberta mas não conseguiu ler frame")
        cap.release()
        
        CameraStatus.objects.create(
            camera=camera,
            status='ERRO_CONEXAO',
            mensagem_erro='Não conseguiu ler frame',
            latencia_ms=int(latencia)
        )
        
        exit(1)
    
    # SUCESSO!
    largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    print("\n" + "="*70)
    print("✅ CONEXÃO ESTABELECIDA COM SUCESSO!")
    print("="*70)
    print(f"\n📊 INFORMAÇÕES DO STREAM:")
    print(f"   Resolução: {largura}x{altura}")
    print(f"   FPS: {fps}")
    print(f"   Latência: {int(latencia)}ms")
    
    # Atualizar câmera
    camera.ultima_conexao = datetime.now()
    camera.status = 'ATIVA'
    camera.resolucao = f"{largura}x{altura}"
    camera.fps = fps
    camera.save()
    
    # Registrar status
    CameraStatus.objects.create(
        camera=camera,
        status='ONLINE',
        qualidade_sinal=100,
        latencia_ms=int(latencia),
        fps_atual=fps
    )
    
    # Salvar frame de teste
    os.makedirs('testes_camera', exist_ok=True)
    arquivo = f"teste_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    caminho = os.path.join('testes_camera', arquivo)
    cv2.imwrite(caminho, frame)
    
    print(f"\n📸 Frame de teste salvo: {arquivo}")
    print(f"   Caminho: {os.path.abspath(caminho)}")
    
    cap.release()
    
    print("\n" + "="*70)
    print("🎯 PRÓXIMO PASSO:")
    print("   Ver vídeo ao vivo: python conectar_camera_verifik.py")
    print("   Opção 3 (Ver vídeo ao vivo)")
    print("="*70 + "\n")

except Exception as e:
    print(f"\n❌ ERRO: {e}")
    
    CameraStatus.objects.create(
        camera=camera,
        status='ERRO_CONEXAO',
        codigo_erro=type(e).__name__,
        mensagem_erro=str(e)
    )
    
    print(f"\nTipo: {type(e).__name__}")
    print("\nVerifique:")
    print("  1. A câmera está ligada?")
    print("  2. Está na mesma rede? (ping 192.168.68.110)")
    print("  3. As credenciais estão corretas?")
