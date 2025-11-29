#!/usr/bin/env python
"""
Teste para verificar se os botões do VerifiK estão funcionando
"""
import requests
import re
import sys

def testar_verifik():
    """Testa se os botões do VerifiK estão funcionando"""
    
    base_url = 'http://127.0.0.1:8000'
    
    print("🔍 Testando Sistema VerifiK...")
    print("=" * 50)
    
    # Criar sessão para manter cookies
    session = requests.Session()
    
    try:
        # 1. Testar página inicial do VerifiK
        print("1. Testando página inicial do VerifiK...")
        response = session.get(f'{base_url}/verifik/')
        if response.status_code == 200:
            print("   ✅ Página inicial OK")
        else:
            print(f"   ❌ Erro na página inicial: {response.status_code}")
            return
            
        # 2. Testar página de login
        print("2. Testando página de login...")
        response = session.get(f'{base_url}/login/')
        if response.status_code == 200:
            print("   ✅ Página de login OK")
            
            # Extrair CSRF token
            csrf_match = re.search(r'name="csrfmiddlewaretoken" value="(.+?)"', response.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
                print(f"   ✅ CSRF token obtido")
                
                # 3. Fazer login
                print("3. Fazendo login como admin...")
                login_data = {
                    'csrfmiddlewaretoken': csrf_token,
                    'username': 'admin',
                    'password': 'admin123'
                }
                
                response = session.post(f'{base_url}/login/', data=login_data)
                if response.status_code == 302 or 'admin' in response.text:
                    print("   ✅ Login realizado com sucesso")
                    
                    # 4. Testar botões específicos
                    print("4. Testando botões do VerifiK...")
                    
                    # Botão: Revisar Fotos
                    print("   4.1 Testando 'Revisar Fotos'...")
                    response = session.get(f'{base_url}/verifik/coleta/revisar-fotos/')
                    if response.status_code == 200:
                        print("   ✅ Revisar Fotos funciona!")
                    else:
                        print(f"   ❌ Erro em Revisar Fotos: {response.status_code}")
                    
                    # Botão: Importar Dataset
                    print("   4.2 Testando 'Importar Dataset'...")
                    response = session.get(f'{base_url}/verifik/coleta/importar-dataset/')
                    if response.status_code == 200:
                        print("   ✅ Importar Dataset funciona!")
                    else:
                        print(f"   ❌ Erro em Importar Dataset: {response.status_code}")
                    
                    # Botão: Anotar Imagem
                    print("   4.3 Testando 'Anotar Produtos'...")
                    response = session.get(f'{base_url}/verifik/coleta/anotar/')
                    if response.status_code == 200:
                        print("   ✅ Anotar Produtos funciona!")
                    else:
                        print(f"   ❌ Erro em Anotar Produtos: {response.status_code}")
                    
                    # Botão: Enviar Fotos
                    print("   4.4 Testando 'Enviar Fotos'...")
                    response = session.get(f'{base_url}/verifik/coleta/enviar-fotos/')
                    if response.status_code == 200:
                        print("   ✅ Enviar Fotos funciona!")
                    else:
                        print(f"   ❌ Erro em Enviar Fotos: {response.status_code}")
                        
                else:
                    print(f"   ❌ Falha no login: {response.status_code}")
            else:
                print("   ❌ CSRF token não encontrado")
        else:
            print(f"   ❌ Erro na página de login: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 Teste concluído!")

if __name__ == '__main__':
    testar_verifik()