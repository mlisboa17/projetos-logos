#!/usr/bin/env python3
"""
Teste básico do scraper standalone - Verificar dependências e conexões
"""

def testar_dependencias():
    """Testa se todas as dependências estão funcionando"""
    print("🔍 VERIFICANDO DEPENDÊNCIAS DO SCRAPER")
    print("="*50)
    
    erros = []
    
    # Teste 1: Playwright
    try:
        from playwright.sync_api import sync_playwright
        print("✅ Playwright importado com sucesso")
    except ImportError as e:
        erros.append(f"❌ Playwright: {e}")
    
    # Teste 2: Requests  
    try:
        import requests
        print(f"✅ Requests {requests.__version__}")
    except ImportError as e:
        erros.append(f"❌ Requests: {e}")
    
    # Teste 3: JSON e outros módulos padrão
    try:
        import json, os, sys, time
        from datetime import datetime
        print("✅ Módulos padrão Python OK")
    except ImportError as e:
        erros.append(f"❌ Módulos padrão: {e}")
    
    # Teste 4: Conexão com sistema principal
    print("\n🌐 TESTANDO CONEXÃO COM SISTEMA PRINCIPAL")
    print("-"*50)
    
    try:
        import requests
        response = requests.get("http://127.0.0.1:8000/fuel/api/status/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sistema principal online: {data['sistema']}")
        else:
            erros.append(f"❌ Sistema retornou HTTP {response.status_code}")
    except requests.exceptions.ConnectionError:
        erros.append("❌ Sistema principal não está rodando (Connection refused)")
    except Exception as e:
        erros.append(f"❌ Erro de conexão: {e}")
    
    # Teste 5: Playwright browser
    print("\n🌐 TESTANDO PLAYWRIGHT BROWSER")
    print("-"*50)
    
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Tentar abrir browser
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.google.com", timeout=10000)
            title = page.title()
            browser.close()
            print(f"✅ Browser funcional - Título: {title}")
    except Exception as e:
        erros.append(f"❌ Browser Playwright: {e}")
        print("💡 Execute: python -m playwright install chromium")
    
    # Resultado final
    print(f"\n{'='*50}")
    if erros:
        print("❌ PROBLEMAS ENCONTRADOS:")
        for erro in erros:
            print(f"   {erro}")
        print(f"\n💡 SOLUÇÕES:")
        print("   1. Instalar dependências: pip install -r requirements_scraper.txt")
        print("   2. Instalar browsers: python -m playwright install chromium")
        print("   3. Iniciar sistema principal: python manage.py runserver")
        return False
    else:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Scraper pronto para uso")
        return True

if __name__ == "__main__":
    testar_dependencias()