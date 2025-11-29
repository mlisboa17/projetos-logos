#!/usr/bin/env python3
"""
Teste da API do scraper - Verificar se o sistema principal está funcionando
"""
import requests
import json

def testar_api():
    """Testa se a API está funcionando"""
    base_url = "http://127.0.0.1:8000/fuel/api"
    
    print("🧪 TESTANDO API DO SISTEMA PRINCIPAL")
    print("="*50)
    
    # Teste 1: Status do sistema
    print("\n[1] Testando status do sistema...")
    try:
        response = requests.get(f"{base_url}/status/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data['status']}")
            print(f"✅ Sistema: {data['sistema']}")
            print(f"✅ Banco: {data['database']}")
            print(f"✅ Postos ativos: {data['estatisticas']['postos_ativos']}")
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Sistema principal não está rodando")
        print("   Execute: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False
    
    # Teste 2: Enviar dados de teste
    print("\n[2] Testando envio de dados...")
    dados_teste = {
        "posto": {
            "codigo_vibra": "95406",
            "cnpj": "04284939000186",
            "razao_social": "AUTO POSTO CASA CAIADA LTDA",
            "nome_fantasia": "AP CASA CAIADA"
        },
        "produtos": [
            {
                "nome": "ETANOL COMUM - TESTE",
                "preco": "Preço: R$ 3,6377",
                "prazo": "30 dias",
                "base": "Base Suape"
            },
            {
                "nome": "GASOLINA ADITIVADA - TESTE", 
                "preco": "Preço: R$ 5,1234",
                "prazo": "15 dias",
                "base": "Base Recife"
            }
        ],
        "modalidade": "FOB"
    }
    
    try:
        response = requests.post(
            f"{base_url}/scraper-data/",
            json=dados_teste,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Status: {result['status']}")
            print(f"✅ Mensagem: {result['message']}")
            detalhes = result['detalhes']
            print(f"✅ Posto: {detalhes['posto_nome']} ({detalhes['posto_codigo']})")
            print(f"✅ Produtos salvos: {detalhes['precos_salvos']}")
            print(f"✅ Erros: {detalhes['precos_erros']}")
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao enviar dados: {e}")
        return False
    
    print("\n🎉 TODOS OS TESTES PASSARAM!")
    print("✅ Sistema principal está pronto para receber dados do scraper")
    return True

if __name__ == "__main__":
    testar_api()