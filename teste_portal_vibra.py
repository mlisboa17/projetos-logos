#!/usr/bin/env python3
"""
SCRAPER VIBRA REAL - TESTE DE CONEXÃO
=====================================

Script para testar conexão real com o portal Vibra
"""

import asyncio
import sys
from playwright.async_api import async_playwright

async def testar_portal_vibra():
    """Testar acesso ao portal Vibra real"""
    
    print("=" * 60)
    print("TESTANDO ACESSO AO PORTAL VIBRA REAL")
    print("=" * 60)
    
    try:
        # Inicializar Playwright
        playwright = await async_playwright().start()
        
        # Lançar browser (visível para debug)
        browser = await playwright.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # Criar página
        page = await browser.new_page()
        
        # URLs possíveis do portal Vibra
        urls_teste = [
            "https://portal.vibra.com.br",
            "https://www.vibra.com.br/portal",
            "https://distribuidora.vibra.com.br",
            "https://login.vibra.com.br"
        ]
        
        print("Testando URLs do portal Vibra...")
        
        for i, url in enumerate(urls_teste, 1):
            try:
                print(f"\n[{i}] Testando: {url}")
                
                # Navegar para URL
                response = await page.goto(url, timeout=15000)
                
                if response and response.status == 200:
                    print(f"    ✅ Status: {response.status}")
                    print(f"    ✅ URL final: {page.url}")
                    
                    # Verificar se é página de login
                    title = await page.title()
                    print(f"    📄 Título: {title}")
                    
                    # Procurar campos de login
                    login_fields = await page.query_selector_all('input[type="password"], input[name*="password"], input[name*="senha"]')
                    
                    if login_fields:
                        print(f"    🔐 Campos de login encontrados: {len(login_fields)}")
                        print("    ✅ Esta parece ser a URL correta para login!")
                        
                        # Manter página aberta para inspeção
                        print("\n🔍 Página mantida aberta para inspeção...")
                        print("Pressione ENTER para continuar...")
                        input()
                        
                        break
                    else:
                        print("    ❌ Campos de login não encontrados")
                        
                else:
                    print(f"    ❌ Status: {response.status if response else 'Sem resposta'}")
                    
            except Exception as e:
                print(f"    ❌ Erro: {e}")
                continue
        
        print("\n" + "=" * 60)
        print("TESTE DE CONEXÃO CONCLUÍDO")
        print("=" * 60)
        
        # Fechar browser
        await browser.close()
        await playwright.stop()
        
        return True
        
    except Exception as e:
        print(f"Erro no teste: {e}")
        return False

async def main():
    """Função principal"""
    print("AVISO: Este script vai abrir um browser real!")
    print("Ele tentará encontrar o portal correto da Vibra.")
    print("")
    
    confirmar = input("Continuar? (S/N): ").upper()
    
    if confirmar == 'S':
        await testar_portal_vibra()
    else:
        print("Teste cancelado.")

if __name__ == "__main__":
    asyncio.run(main())