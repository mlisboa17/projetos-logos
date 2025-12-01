"""
Testa múltiplas URLs RTSP para encontrar a correta
"""
import cv2
from datetime import datetime

IP = "192.168.68.110"
USUARIO = "E6803"
SENHA = "C@sa3863"

print("="*70)
print("🔍 PROCURANDO URL RTSP CORRETA - INTELBRAS")
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
    f"rtsp://{USUARIO}:{SENHA}@{IP}:554/user={USUARIO}&password={SENHA}&channel=1&stream=0.sdp",
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
                
                # Salvar configuração
                with open("camera_url_correta.txt", "w") as f:
                    f.write(f"URL: {url}\n")
                    f.write(f"Resolucao: {largura}x{altura}\n")
                    f.write(f"FPS: {fps}\n")
                
                print("\n✅ Configuração salva em: camera_url_correta.txt\n")
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
print("\nPossíveis causas:")
print("  1. Porta 554 bloqueada por firewall")
print("  2. RTSP desabilitado na câmera")
print("  3. Credenciais incorretas")
print("  4. Modelo/firmware diferente")
print("\nTente:")
print("  - Acessar a câmera pelo navegador: http://192.168.68.110")
print("  - Verificar configurações RTSP no app Mibo")
print("  - Testar com VLC: Media > Open Network Stream")
