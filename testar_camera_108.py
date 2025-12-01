"""
Testa câmera no IP 192.168.68.108
"""
import cv2
from datetime import datetime

IP = "192.168.68.108"
CREDENCIAIS = [
    ("admin", "C@sa3863"),
    ("E6803", "C@sa3863"),
    ("admin", "admin"),
    ("admin", ""),
]

print("="*70)
print(f"🔍 TESTANDO CÂMERA: {IP}")
print("="*70)

for usuario, senha in CREDENCIAIS:
    print(f"\n{'='*70}")
    print(f"🔑 Testando: {usuario} / {senha if senha else '(vazio)'}")
    print(f"{'='*70}")
    
    # URLs comuns para Intelbras
    urls = [
        f"rtsp://{usuario}:{senha}@{IP}:554/cam/realmonitor?channel=1&subtype=0",
        f"rtsp://{usuario}:{senha}@{IP}:554/cam/realmonitor?channel=1&subtype=1",
        f"rtsp://{usuario}:{senha}@{IP}:554/",
        f"rtsp://{usuario}:{senha}@{IP}:554/live/ch00_0",
    ]
    
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] {url[:65]}...")
        
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
                    print(f"\n📍 IP: {IP}")
                    print(f"👤 Usuário: {usuario}")
                    print(f"🔑 Senha: {senha}")
                    print(f"\n🎯 URL FUNCIONAL:")
                    print(f"    {url}")
                    print(f"\n📊 INFORMAÇÕES:")
                    print(f"    Resolução: {largura}x{altura}")
                    print(f"    FPS: {fps}")
                    print("="*70)
                    
                    # Salvar frame
                    import os
                    os.makedirs('testes_camera', exist_ok=True)
                    arquivo = f"camera_{IP.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    caminho = os.path.join('testes_camera', arquivo)
                    cv2.imwrite(caminho, frame)
                    print(f"\n📸 Frame salvo: {arquivo}")
                    
                    cap.release()
                    
                    # Atualizar/criar câmera no banco
                    import os
                    import django
                    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
                    django.setup()
                    
                    from verifik.models import Camera, CameraStatus
                    from accounts.models import Organization
                    
                    org = Organization.objects.first()
                    
                    camera, created = Camera.objects.update_or_create(
                        ip_address=IP,
                        defaults={
                            'organization': org,
                            'nome': f'Câmera Intelbras {IP}',
                            'localizacao': 'Detectada automaticamente',
                            'porta': 554,
                            'usuario': usuario,
                            'senha': senha,
                            'url_stream': url,
                            'resolucao': f"{largura}x{altura}",
                            'fps': fps,
                            'ultima_conexao': datetime.now(),
                            'status': 'ATIVA',
                            'ativa': True
                        }
                    )
                    
                    CameraStatus.objects.create(
                        camera=camera,
                        status='ONLINE',
                        qualidade_sinal=100,
                        fps_atual=fps
                    )
                    
                    action = "criada" if created else "atualizada"
                    print(f"\n✅ Câmera {action} no banco de dados!")
                    print(f"   ID: {camera.id}")
                    print(f"   Nome: {camera.nome}")
                    
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
            if "401" in str(e) or "Unauthorized" in str(e):
                print(f"    ❌ 401 Unauthorized")
            else:
                print(f"    ❌ Erro: {type(e).__name__}")

print("\n" + "="*70)
print("❌ NENHUMA CREDENCIAL FUNCIONOU")
print("="*70)
print(f"\nCâmera {IP} está online mas não conseguimos autenticar.")
print("Verifique as credenciais no app Mibo ou acesse:")
print(f"  http://{IP}")
