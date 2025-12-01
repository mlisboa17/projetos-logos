"""
Script para conectar e testar câmeras do sistema VerifiK
Usa os dados das câmeras cadastradas no banco de dados Django
"""

import os
import django
import cv2
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import Camera, CameraStatus
from accounts.models import Organization


def testar_conexao_camera(camera):
    """
    Testa conexão com uma câmera específica
    
    Args:
        camera: Objeto Camera do Django
        
    Returns:
        dict: Resultado do teste com status, fps, resolução, etc.
    """
    print(f"\n{'='*70}")
    print(f"🎥 Testando: {camera.nome} ({camera.localizacao})")
    print(f"{'='*70}")
    print(f"IP: {camera.ip_address}:{camera.porta}")
    print(f"URL: {camera.url_stream}")
    print(f"Status atual: {camera.get_status_display()}")
    
    resultado = {
        'camera': camera,
        'sucesso': False,
        'mensagem': '',
        'fps': None,
        'resolucao': None,
        'latencia_ms': None
    }
    
    try:
        # Tentar conectar
        print(f"\n⏳ Conectando...")
        inicio = datetime.now()
        
        cap = cv2.VideoCapture(camera.url_stream)
        
        if not cap.isOpened():
            resultado['mensagem'] = "Não foi possível abrir a conexão"
            print(f"❌ {resultado['mensagem']}")
            
            # Registrar status de erro
            CameraStatus.objects.create(
                camera=camera,
                status='ERRO_CONEXAO',
                mensagem_erro=resultado['mensagem']
            )
            
            return resultado
        
        # Tentar ler um frame
        ret, frame = cap.read()
        
        fim = datetime.now()
        latencia = (fim - inicio).total_seconds() * 1000  # em ms
        
        if not ret or frame is None:
            resultado['mensagem'] = "Conexão aberta mas não conseguiu ler frame"
            print(f"⚠️ {resultado['mensagem']}")
            cap.release()
            
            CameraStatus.objects.create(
                camera=camera,
                status='ERRO_CONEXAO',
                mensagem_erro=resultado['mensagem'],
                latencia_ms=int(latencia)
            )
            
            return resultado
        
        # SUCESSO! Obter informações
        largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        resultado['sucesso'] = True
        resultado['fps'] = fps
        resultado['resolucao'] = f"{largura}x{altura}"
        resultado['latencia_ms'] = int(latencia)
        
        print(f"\n✅ CONEXÃO ESTABELECIDA!")
        print(f"   Resolução: {largura}x{altura}")
        print(f"   FPS: {fps}")
        print(f"   Latência: {int(latencia)}ms")
        
        # Atualizar câmera no banco
        camera.ultima_conexao = datetime.now()
        camera.status = 'ATIVA'
        camera.resolucao = f"{largura}x{altura}"
        camera.fps = fps
        camera.save()
        
        # Registrar status online
        CameraStatus.objects.create(
            camera=camera,
            status='ONLINE',
            qualidade_sinal=100,
            latencia_ms=int(latencia),
            fps_atual=fps
        )
        
        # Salvar frame de teste
        pasta_testes = os.path.join(os.path.dirname(__file__), 'testes_camera')
        os.makedirs(pasta_testes, exist_ok=True)
        
        nome_arquivo = f"{camera.nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        caminho = os.path.join(pasta_testes, nome_arquivo)
        cv2.imwrite(caminho, frame)
        
        print(f"   Frame salvo: {nome_arquivo}")
        
        cap.release()
        
    except Exception as e:
        resultado['mensagem'] = f"Erro: {str(e)}"
        print(f"❌ {resultado['mensagem']}")
        
        # Registrar erro
        CameraStatus.objects.create(
            camera=camera,
            status='ERRO_CONEXAO',
            codigo_erro=type(e).__name__,
            mensagem_erro=str(e)
        )
    
    return resultado


def conectar_camera_stream(camera, exibir_video=True, duracao_segundos=10):
    """
    Conecta à câmera e exibe o vídeo em tempo real
    
    Args:
        camera: Objeto Camera do Django
        exibir_video: Se True, abre janela com vídeo
        duracao_segundos: Tempo para exibir (0 = infinito)
    """
    print(f"\n{'='*70}")
    print(f"🎥 Conectando ao stream: {camera.nome}")
    print(f"{'='*70}")
    
    cap = cv2.VideoCapture(camera.url_stream)
    
    if not cap.isOpened():
        print("❌ Não foi possível conectar à câmera")
        return False
    
    print("✅ Conectado! Exibindo vídeo...")
    print(f"   Pressione 'q' para sair")
    print(f"   Pressione 's' para salvar frame")
    
    inicio = datetime.now()
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("⚠️ Erro ao ler frame")
                break
            
            frame_count += 1
            
            # Adicionar informações no frame
            tempo_decorrido = (datetime.now() - inicio).total_seconds()
            texto = f"{camera.nome} | {datetime.now().strftime('%H:%M:%S')} | Frame {frame_count}"
            cv2.putText(frame, texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.7, (0, 255, 0), 2)
            
            if exibir_video:
                cv2.imshow(f'VerifiK - {camera.nome}', frame)
            
            # Verificar teclas
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\n👋 Saindo...")
                break
            elif key == ord('s'):
                # Salvar frame
                pasta_capturas = os.path.join(os.path.dirname(__file__), 'capturas_camera')
                os.makedirs(pasta_capturas, exist_ok=True)
                
                nome = f"{camera.nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                caminho = os.path.join(pasta_capturas, nome)
                cv2.imwrite(caminho, frame)
                print(f"📸 Frame salvo: {nome}")
            
            # Verificar tempo limite
            if duracao_segundos > 0 and tempo_decorrido >= duracao_segundos:
                print(f"\n⏱️ Tempo limite atingido ({duracao_segundos}s)")
                break
        
        # Atualizar última detecção
        camera.ultima_deteccao = datetime.now()
        camera.save()
        
        print(f"\n📊 Estatísticas:")
        print(f"   Frames capturados: {frame_count}")
        print(f"   Tempo total: {tempo_decorrido:.1f}s")
        print(f"   FPS médio: {frame_count/tempo_decorrido:.1f}")
        
    finally:
        cap.release()
        cv2.destroyAllWindows()
    
    return True


def listar_cameras(organization_id=None):
    """Lista todas as câmeras cadastradas"""
    print(f"\n{'='*70}")
    print("📷 CÂMERAS CADASTRADAS")
    print(f"{'='*70}\n")
    
    if organization_id:
        cameras = Camera.objects.filter(organization_id=organization_id)
    else:
        cameras = Camera.objects.all()
    
    if not cameras.exists():
        print("❌ Nenhuma câmera cadastrada")
        return []
    
    for i, cam in enumerate(cameras, 1):
        print(f"{i}. {cam.nome}")
        print(f"   📍 Local: {cam.localizacao}")
        print(f"   🌐 IP: {cam.ip_address}:{cam.porta}")
        print(f"   📊 Status: {cam.get_status_display()}")
        print(f"   🏢 Organização: {cam.organization.name if cam.organization else 'N/A'}")
        if cam.ultima_conexao:
            print(f"   🕒 Última conexão: {cam.ultima_conexao.strftime('%d/%m/%Y %H:%M')}")
        print()
    
    return list(cameras)


def menu_principal():
    """Menu interativo para testar câmeras"""
    print("\n" + "="*70)
    print("🎥 SISTEMA DE TESTE DE CÂMERAS - VERIFIK")
    print("="*70)
    
    while True:
        print("\n📋 MENU:")
        print("1. Listar todas as câmeras")
        print("2. Testar conexão de uma câmera")
        print("3. Ver vídeo ao vivo de uma câmera")
        print("4. Testar todas as câmeras")
        print("5. Cadastrar nova câmera")
        print("0. Sair")
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "1":
            listar_cameras()
        
        elif opcao == "2":
            cameras = listar_cameras()
            if cameras:
                try:
                    idx = int(input("\nNúmero da câmera: ")) - 1
                    if 0 <= idx < len(cameras):
                        testar_conexao_camera(cameras[idx])
                    else:
                        print("❌ Número inválido")
                except ValueError:
                    print("❌ Digite um número válido")
        
        elif opcao == "3":
            cameras = listar_cameras()
            if cameras:
                try:
                    idx = int(input("\nNúmero da câmera: ")) - 1
                    if 0 <= idx < len(cameras):
                        conectar_camera_stream(cameras[idx], exibir_video=True, duracao_segundos=0)
                    else:
                        print("❌ Número inválido")
                except ValueError:
                    print("❌ Digite um número válido")
        
        elif opcao == "4":
            cameras = listar_cameras()
            if cameras:
                print(f"\n🔄 Testando {len(cameras)} câmera(s)...\n")
                resultados = []
                for cam in cameras:
                    resultado = testar_conexao_camera(cam)
                    resultados.append(resultado)
                
                # Resumo
                print(f"\n{'='*70}")
                print("📊 RESUMO DOS TESTES")
                print(f"{'='*70}")
                sucesso = sum(1 for r in resultados if r['sucesso'])
                print(f"✅ Online: {sucesso}/{len(resultados)}")
                print(f"❌ Offline: {len(resultados) - sucesso}/{len(resultados)}")
        
        elif opcao == "5":
            print("\n📝 CADASTRAR NOVA CÂMERA")
            print("-" * 70)
            
            # Listar organizações
            orgs = Organization.objects.all()
            print("\nOrganizações disponíveis:")
            for i, org in enumerate(orgs, 1):
                print(f"{i}. {org.name}")
            
            try:
                org_idx = int(input("\nNúmero da organização: ")) - 1
                organization = orgs[org_idx]
                
                nome = input("Nome da câmera: ")
                localizacao = input("Localização (ex: Caixa 1): ")
                ip = input("IP da câmera: ")
                porta = input("Porta (padrão 554): ").strip() or "554"
                usuario = input("Usuário: ")
                senha = input("Senha: ")
                
                # Montar URL RTSP
                url = f"rtsp://{usuario}:{senha}@{ip}:{porta}/cam/realmonitor?channel=1&subtype=0"
                
                camera = Camera.objects.create(
                    organization=organization,
                    nome=nome,
                    localizacao=localizacao,
                    ip_address=ip,
                    porta=int(porta),
                    usuario=usuario,
                    senha=senha,
                    url_stream=url,
                    status='ATIVA',
                    ativa=True
                )
                
                print(f"\n✅ Câmera '{nome}' cadastrada com sucesso!")
                print(f"   ID: {camera.id}")
                print(f"   URL: {url}")
                
                # Testar imediatamente
                testar = input("\nTestar conexão agora? (s/n): ").lower()
                if testar == 's':
                    testar_conexao_camera(camera)
                
            except (ValueError, IndexError):
                print("❌ Erro ao cadastrar câmera")
        
        elif opcao == "0":
            print("\n👋 Até logo!")
            break
        
        else:
            print("❌ Opção inválida")


if __name__ == '__main__':
    menu_principal()
