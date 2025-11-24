"""
╔══════════════════════════════════════════════════════════════════╗
║              TESTE - API DE DETECÇÃO VERIFIK                     ║
║         Valida se a API está funcionando corretamente            ║
╚══════════════════════════════════════════════════════════════════╝

📋 TESTES:
1. ✅ Endpoint está online
2. ✅ YOLO instalado
3. ✅ Modelo carregado
4. ✅ Detecção funciona (imagem teste)
5. ✅ Resposta JSON correta

🚀 USO:
python testar_api_deteccao.py
"""

import sys
import os
import base64
import requests
from pathlib import Path

# Adicionar projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken


def criar_token_teste():
    """Cria token JWT para teste"""
    User = get_user_model()
    
    # Buscar ou criar usuário teste
    user, created = User.objects.get_or_create(
        username='teste_api',
        defaults={
            'email': 'teste@verifik.com',
            'is_active': True
        }
    )
    
    if created:
        user.set_password('teste123')
        user.save()
        print("✅ Usuário teste criado")
    
    # Gerar token
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


def testar_status_api():
    """Testa se API está online"""
    print("\n" + "="*70)
    print("1️⃣  TESTE: Status da API")
    print("="*70)
    
    try:
        response = requests.get('http://localhost:8000/api/verifik/detectar/teste/')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API online")
            print(f"   Modelo: {data.get('modelo')}")
            print(f"   Modelo existe: {data.get('modelo_existe')}")
            print(f"   YOLO disponível: {data.get('yolo_disponivel')}")
            print(f"   Produtos: {data.get('produtos_cadastrados')}")
            print(f"   Confiança mínima: {data.get('confianca_minima')}")
            return True
        else:
            print(f"❌ API retornou status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Servidor não está rodando!")
        print("   Execute: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def testar_deteccao_imagem_base():
    """Testa detecção com imagem simples (quadrado vermelho)"""
    print("\n" + "="*70)
    print("2️⃣  TESTE: Detecção com imagem teste")
    print("="*70)
    
    try:
        import cv2
        import numpy as np
        
        # Criar imagem teste (quadrado vermelho 300x300)
        img = np.zeros((300, 300, 3), dtype=np.uint8)
        img[50:250, 50:250] = [0, 0, 255]  # Vermelho em BGR
        
        # Codificar para base64
        _, buffer = cv2.imencode('.jpg', img)
        img_base64 = base64.b64encode(buffer).decode()
        
        # Obter token
        token = criar_token_teste()
        
        # Fazer requisição
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'imagem': f'data:image/jpeg;base64,{img_base64}',
            'salvar': False
        }
        
        response = requests.post(
            'http://localhost:8000/api/verifik/detectar/',
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Detecção executada")
            print(f"   Status: {data.get('status')}")
            print(f"   Detecções: {data.get('total_detectado')}")
            print(f"   Tempo: {data.get('tempo_processamento')}s")
            
            if data.get('deteccoes'):
                print(f"\n   📦 Produtos detectados:")
                for det in data['deteccoes']:
                    print(f"      - {det['produto_nome']} ({det['confianca']*100:.0f}%)")
            else:
                print(f"   ℹ️  Nenhum produto detectado (normal para imagem teste)")
            
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except ImportError:
        print("⚠️  OpenCV não instalado. Pule este teste.")
        print("   Instale: pip install opencv-python")
        return None
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def verificar_dependencias():
    """Verifica se dependências estão instaladas"""
    print("\n" + "="*70)
    print("3️⃣  VERIFICAÇÃO: Dependências")
    print("="*70)
    
    deps = {
        'ultralytics': False,
        'cv2': False,
        'PIL': False,
        'numpy': False
    }
    
    for dep in deps:
        try:
            __import__(dep)
            deps[dep] = True
            print(f"✅ {dep} instalado")
        except ImportError:
            print(f"❌ {dep} NÃO instalado")
    
    print(f"\n📊 Resultado: {sum(deps.values())}/{len(deps)} dependências OK")
    
    if not deps['ultralytics']:
        print("\n⚠️  ULTRALYTICS AUSENTE - Instale:")
        print("   pip install ultralytics")
    
    if not deps['cv2']:
        print("\n⚠️  OPENCV AUSENTE - Instale:")
        print("   pip install opencv-python")


def main():
    """Executa todos os testes"""
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║          TESTE COMPLETO - API DETECÇÃO VERIFIK                   ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    
    # Verificar dependências
    verificar_dependencias()
    
    # Testar status
    api_ok = testar_status_api()
    
    if api_ok:
        # Testar detecção
        testar_deteccao_imagem_base()
    
    print("\n" + "="*70)
    print("✅ TESTES CONCLUÍDOS")
    print("="*70)
    
    print("\n💡 PRÓXIMOS PASSOS:")
    print("   1. Treinar modelo YOLO com produtos reais")
    print("   2. Testar com foto de Heineken 330ml")
    print("   3. Integrar com câmeras ao vivo")
    print("   4. Criar interface web de teste")


if __name__ == '__main__':
    main()
