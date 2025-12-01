"""
Testa com credenciais admin / C@sa3863
"""
import cv2
from datetime import datetime

IP = "192.168.68.110"
USUARIO = "admin"
SENHA = "C@sa3863"

print("="*70)
print("🔍 TESTANDO COM CREDENCIAIS: admin / C@sa3863")
print("="*70)
print(f"IP: {IP}")
print(f"Usuário: {USUARIO}")
print(f"Senha: {SENHA}")
print()

# URLs comuns para Intelbras
urls = [
    f"rtsp://{USUARIO}:{SENHA}@{IP}:554/cam/realmonitor?channel=1&subtype=0",
    f"rtsp://{USUARIO}:{SENHA}@{IP}:554/cam/realmonitor?channel=1&subtype=1",
    f"rtsp://{USUARIO}:{SENHA}@{IP}:554/",
    f"rtsp://{USUARIO}:{SENHA}@{IP}:554/live/ch00_0",
    f"rtsp://{USUARIO}:{SENHA}@{IP}:554/h264",
    f"rtsp://{USUARIO}:{SENHA}@{IP}:554/Streaming/Channels/101",
    f"rtsp://{USUARIO}:{SENHA}@{IP}:554/Streaming/Channels/1",
]

for i, url in enumerate(urls, 1):
    print(f"\n[{i}/{len(urls)}] Testando...")
    print(f"    {url[:70]}...")
    
    try:
        cap = cv2.VideoCapture(url)
        
        if cap.isOpened():
            ret, frame = cap.read()
            
            if ret and frame is not None:
                largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                
                print("\n" + "="*70)
                print("✅✅✅ CONEXÃO ESTABELECIDA COM SUCESSO! ✅✅✅")
                print("="*70)
                print(f"\n🎯 URL FUNCIONAL:")
                print(f"    {url}")
                print(f"\n📊 INFORMAÇÕES:")
                print(f"    Resolução: {largura}x{altura}")
                print(f"    FPS: {fps}")
                print("="*70)
                
                # Salvar frame
                import os
                os.makedirs('testes_camera', exist_ok=True)
                arquivo = f"camera_funcionando_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                caminho = os.path.join('testes_camera', arquivo)
                cv2.imwrite(caminho, frame)
                print(f"\n📸 Frame salvo: {arquivo}")
                
                cap.release()
                
                # Atualizar câmera no banco
                import os
                import django
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
                django.setup()
                
                from verifik.models import Camera, CameraStatus
                
                camera = Camera.objects.first()
                if camera:
                    camera.usuario = USUARIO
                    camera.senha = SENHA
                    camera.url_stream = url
                    camera.resolucao = f"{largura}x{altura}"
                    camera.fps = fps
                    camera.ultima_conexao = datetime.now()
                    camera.status = 'ATIVA'
                    camera.save()
                    
                    CameraStatus.objects.create(
                        camera=camera,
                        status='ONLINE',
                        qualidade_sinal=100,
                        fps_atual=fps
                    )
                    
                    print("\n✅ Câmera atualizada no banco de dados!")
                
                print("\n" + "="*70)
                print("🎯 PRÓXIMOS PASSOS:")
                print("   1. Ver vídeo: python conectar_camera_verifik.py (opção 3)")
                print("   2. Detectar produtos: python exemplo_deteccao_camera.py")
                print("="*70 + "\n")
                
                exit(0)
            
            cap.release()
            print("    ⚠️ Abriu mas não leu frame")
        else:
            print("    ❌ Não conectou")
            
    except Exception as e:
        print(f"    ❌ Erro: {type(e).__name__}")

print("\n" + "="*70)
print("❌ NENHUMA URL FUNCIONOU")
print("="*70)
print("\nVerifique:")
print("  - Credenciais no app Mibo")
print("  - Acesse http://192.168.68.110 no navegador")
