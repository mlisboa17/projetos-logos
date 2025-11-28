#!/usr/bin/env python3
"""
SCRAPER VIBRA ENERGIA - EXECUTÁVEL STANDALONE
Sistema independente que coleta preços dos postos e alimenta o banco principal
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

class VibraScraperStandalone:
    """Scraper standalone para executável"""
    
    def __init__(self, username='95406', password='Apcc2350', headless=True):
        """
        Inicializa o scraper standalone
        
        Args:
            username: Login do portal Vibra (padrão: Casa Caiada)
            password: Senha do portal Vibra
            headless: True = sem interface gráfica, False = mostra navegador
        """
        self.username = username
        self.password = password
        self.headless = headless
        self.login_url = "https://cn.vibraenergia.com.br/login/"
        
        # URL do sistema principal (Django) para enviar dados
        self.api_url_base = "http://127.0.0.1:8000/api"  # Altere se necessário
        
        # Lista completa dos 11 postos do Grupo Lisboa
        self.todos_postos = {
            '95406': {'codigo': '95406', 'razao': 'AUTO POSTO CASA CAIADA LTDA', 'nome': 'AP CASA CAIADA', 'cnpj': '04284939000186'},
            '107469': {'codigo': '107469', 'razao': 'POSTO ENSEADA DO NORTE LTDA', 'nome': 'POSTO ENSEADA DO NOR', 'cnpj': '00338804000103'},
            '11236': {'codigo': '11236', 'razao': 'REAL RECIFE LTDA', 'nome': 'POSTO REAL', 'cnpj': '24156978000105'},
            '1153963': {'codigo': '1153963', 'razao': 'POSTO CIDADE PATRIMONIO LTDA', 'nome': 'POSTO AVENIDA', 'cnpj': '05428059000280'},
            '124282': {'codigo': '124282', 'razao': 'R.J. COMBUSTIVEIS E LUBRIFICANTES L', 'nome': 'R J', 'cnpj': '08726064000186'},
            '14219': {'codigo': '14219', 'razao': 'AUTO POSTO GLOBO LTDA', 'nome': 'GLOBO105', 'cnpj': '41043647000188'},
            '156075': {'codigo': '156075', 'razao': 'DISTRIBUIDORA R S DERIVADO DE PETRO', 'nome': 'POSTO BR SHOPPING', 'cnpj': '07018760000175'},
            '1775869': {'codigo': '1775869', 'razao': 'POSTO DOZE COMERCIO DE COMBUSTIVEIS', 'nome': 'POSTO DOZE', 'cnpj': '52308604000101'},
            '5039': {'codigo': '5039', 'razao': 'RIO DOCE COMERCIO E SERVICOS LTDA', 'nome': 'POSTO VIP', 'cnpj': '03008754000186'},
            '61003': {'codigo': '61003', 'razao': 'AUTO POSTO IGARASSU LTDA.', 'nome': 'P IGARASSU', 'cnpj': '04274378000134'},
            '94762': {'codigo': '94762', 'razao': 'POSTO CIDADE PATRIMONIO LTDA', 'nome': 'CIDADE PATRIMONIO', 'cnpj': '05428059000107'},
        }
    
    def log(self, message):
        """Log com timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def close_popups(self, page, max_attempts=15):
        """Fecha todos os popups/banners que aparecem após login"""
        self.log("Fechando modais...")
        
        modals_fechados = 0
        tentativas_vazias = 0
        
        for attempt in range(max_attempts):
            modal_encontrado = False
            
            try:
                continuar = page.get_by_role("button", name="Continuar")
                if continuar.count() > 0:
                    if continuar.first.is_visible(timeout=500):
                        continuar.first.click()
                        modals_fechados += 1
                        time.sleep(0.8)
                        modal_encontrado = True
                        continue
            except:
                pass
            
            try:
                checkbox = page.locator('input[name*="j_idt"]')
                if checkbox.count() > 0 and checkbox.first.is_visible(timeout=300):
                    checkbox.first.click()
                    time.sleep(0.3)
                    continuar2 = page.get_by_role("button", name="Continuar")
                    if continuar2.count() > 0 and continuar2.first.is_visible(timeout=300):
                        continuar2.first.click()
                        modals_fechados += 1
                        time.sleep(0.8)
                        modal_encontrado = True
            except:
                pass
            
            try:
                page.keyboard.press('Escape')
                time.sleep(0.2)
            except:
                pass
            
            if not modal_encontrado:
                tentativas_vazias += 1
                if tentativas_vazias >= 2:
                    break
            else:
                tentativas_vazias = 0
        
        self.log(f"{modals_fechados} modal(is) fechado(s)")
    
    def login(self, page):
        """Faz login no portal"""
        self.log(f"Fazendo login com usuário {self.username}...")
        
        page.goto(self.login_url)
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        
        # Preencher usuário
        user_selectors = [
            'input[name="usuario"]', 'input[name="username"]', 'input[name="user"]',
            'input[name="login"]', 'input[type="text"]', 'input#username'
        ]
        
        user_filled = False
        for selector in user_selectors:
            try:
                if page.locator(selector).is_visible(timeout=2000):
                    page.fill(selector, self.username)
                    user_filled = True
                    break
            except:
                continue
        
        if not user_filled:
            raise Exception("Campo de usuário não encontrado")
        
        # Preencher senha
        pass_selectors = [
            'input[name="senha"]', 'input[name="password"]', 'input[type="password"]'
        ]
        
        pass_filled = False
        for selector in pass_selectors:
            try:
                if page.locator(selector).is_visible(timeout=2000):
                    page.fill(selector, self.password)
                    pass_filled = True
                    break
            except:
                continue
        
        if not pass_filled:
            raise Exception("Campo de senha não encontrado")
        
        # Clicar em entrar
        button_selectors = [
            'button[type="submit"]', 'button:has-text("Entrar")', 'input[type="submit"]'
        ]
        
        button_clicked = False
        for selector in button_selectors:
            try:
                if page.locator(selector).is_visible(timeout=2000):
                    page.click(selector)
                    button_clicked = True
                    break
            except:
                continue
        
        if not button_clicked:
            page.press(pass_selectors[0], 'Enter')
        
        try:
            page.wait_for_load_state('networkidle', timeout=60000)
        except:
            pass
        
        time.sleep(2)
        self.close_popups(page, max_attempts=25)
        time.sleep(2)
        self.close_popups(page, max_attempts=10)
        
        self.log("Login realizado com sucesso")
    
    def trocar_posto(self, page, cnpj_posto):
        """Troca o posto selecionado usando o CNPJ"""
        self.log(f"Trocando para posto CNPJ: {cnpj_posto}...")
        
        try:
            page.get_by_text("import_export").click()
            time.sleep(1)
            
            page.get_by_role("textbox", name="Buscar empresa").click()
            time.sleep(0.5)
            page.get_by_role("textbox", name="Buscar empresa").fill(cnpj_posto)
            page.get_by_role("textbox", name="Buscar empresa").press("Enter")
            time.sleep(0.5)
            
            page.locator(".mat-radio-outer-circle").click()
            time.sleep(0.5)
            
            page.get_by_role("button", name="Confirmar").click()
            time.sleep(3)
            
            try:
                page.wait_for_load_state('networkidle', timeout=30000)
            except:
                pass
            
            time.sleep(2)
            self.log(f"Posto trocado para CNPJ: {cnpj_posto}")
            return True
            
        except Exception as e:
            self.log(f"Erro ao trocar posto: {e}")
            raise
    
    def navegar_pedidos(self, page):
        """Navega para seção de Pedidos"""
        self.log("Navegando para Pedidos...")
        
        try:
            pedidos_btn = page.get_by_role("button", name="Pedidos")
            
            if pedidos_btn.count() > 0 and pedidos_btn.first.is_visible(timeout=5000):
                pedidos_btn.first.click()
            else:
                time.sleep(1)
                if pedidos_btn.count() > 0:
                    pedidos_btn.first.click()
                else:
                    page.locator('a:has-text("Pedidos")').first.click()
                
        except Exception as e:
            self.log(f"Erro ao navegar: {e}")
            raise
        
        try:
            page.wait_for_load_state('networkidle', timeout=60000)
        except:
            pass
        
        time.sleep(1.5)
        
        # Selecionar modalidade FOB
        self.log("Selecionando modalidade FOB...")
        try:
            modalidade_dropdown = page.get_by_text("Modalidade", exact=False).first
            if modalidade_dropdown.is_visible(timeout=3000):
                modalidade_dropdown.click()
                time.sleep(0.5)
                
                fob_option = page.locator("#mat-option-3").get_by_text("FOB")
                if fob_option.is_visible(timeout=2000):
                    fob_option.first.click()
                    time.sleep(1)
                else:
                    page.get_by_text("FOB", exact=True).first.click()
                    time.sleep(1)
        except Exception as e:
            self.log(f"Erro ao selecionar modalidade: {e}")
    
    def extrair_produtos(self, page):
        """Extrai informações dos produtos da página"""
        self.log("Extraindo produtos...")
        
        # Aguardar produtos carregarem
        try:
            page.wait_for_selector("app-item-vitrine", timeout=15000)
            time.sleep(2)
        except:
            self.log("Timeout aguardando produtos")
        
        # Scroll para carregar todos
        last_height = page.evaluate("document.body.scrollHeight")
        while True:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1.5)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.5)
        
        # Extrair cards de produtos
        try:
            cards = page.locator("app-item-vitrine").all()
            self.log(f"Encontrados {len(cards)} produtos")
        except:
            self.log("Nenhum produto encontrado")
            return []
        
        produtos = []
        produtos_unicos = {}
        
        for i, card in enumerate(cards, 1):
            try:
                texto_card = card.inner_text()
                
                if 'indisponível' in texto_card.lower():
                    continue
                
                produto_info = {
                    'nome': None,
                    'preco': None,
                    'prazo': None,
                    'base': None
                }
                
                linhas = [l.strip() for l in texto_card.split('\n') if l.strip()]
                
                for idx, linha in enumerate(linhas):
                    linha_lower = linha.lower()
                    
                    # Nome do produto
                    if not produto_info['nome']:
                        if any(comb in linha_lower for comb in ['etanol', 'gasolina', 'diesel', 'arla', 'gnv']):
                            produto_info['nome'] = linha
                        elif idx == 0 and linha_lower not in ['disponível', 'em estoque']:
                            produto_info['nome'] = linha
                    
                    # Preço
                    if 'r$' in linha_lower or 'preço:' in linha_lower:
                        if not produto_info['preco']:
                            produto_info['preco'] = linha
                    
                    # Prazo
                    if 'dia' in linha_lower and 'prazo' not in linha_lower:
                        if not produto_info['prazo']:
                            produto_info['prazo'] = linha
                    
                    # Base
                    if 'base' in linha_lower:
                        produto_info['base'] = linha
                
                if produto_info['nome'] and produto_info['nome'] not in produtos_unicos:
                    produtos_unicos[produto_info['nome']] = produto_info
                
            except Exception as e:
                self.log(f"Erro ao processar card {i}: {e}")
                continue
        
        produtos = list(produtos_unicos.values())
        self.log(f"Total extraído: {len(produtos)} produtos disponíveis")
        
        return produtos
    
    def enviar_dados_para_sistema(self, dados_posto):
        """
        Envia dados coletados para o sistema principal via API
        
        Args:
            dados_posto: Dicionário com dados do posto e produtos
        """
        try:
            # Endpoint para receber dados do scraper
            url = f"{self.api_url_base}/fuel/scraper-data/"
            
            # Dados para enviar
            payload = {
                'posto': {
                    'codigo_vibra': dados_posto['codigo'],
                    'cnpj': dados_posto['cnpj'],
                    'razao_social': dados_posto['razao'],
                    'nome_fantasia': dados_posto['nome']
                },
                'produtos': dados_posto['produtos'],
                'data_coleta': datetime.now().isoformat(),
                'modalidade': 'FOB'
            }
            
            # Enviar via POST
            response = requests.post(
                url,
                json=payload,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                self.log(f"✅ Dados enviados com sucesso para o sistema principal")
                return True
            else:
                self.log(f"❌ Erro HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            self.log("❌ Erro: Sistema principal não está rodando (Connection refused)")
            return False
        except Exception as e:
            self.log(f"❌ Erro ao enviar dados: {e}")
            return False
    
    def salvar_backup_local(self, dados_consolidados):
        """Salva backup local dos dados coletados"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_scraper_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(dados_consolidados, f, ensure_ascii=False, indent=2)
            
            self.log(f"💾 Backup salvo: {filename}")
            return filename
            
        except Exception as e:
            self.log(f"❌ Erro ao salvar backup: {e}")
            return None
    
    def verificar_e_instalar_browser(self):
        """Verifica se o browser está instalado e instala se necessário"""
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                # Testar se consegue abrir browser
                browser = p.chromium.launch(headless=True)
                browser.close()
                return True
        except Exception as e:
            error_msg = str(e)
            if "Executable doesn't exist" in error_msg or "Please run the following command" in error_msg:
                self.log("⚠️ Browser Playwright não encontrado. Instalando...")
                try:
                    import subprocess
                    import sys
                    
                    # Tentar instalar browser
                    result = subprocess.run([
                        sys.executable, "-m", "playwright", "install", "chromium"
                    ], capture_output=True, text=True, timeout=300)
                    
                    if result.returncode == 0:
                        self.log("✅ Browser instalado com sucesso")
                        return True
                    else:
                        self.log(f"❌ Erro ao instalar browser: {result.stderr}")
                        return False
                        
                except subprocess.TimeoutExpired:
                    self.log("❌ Timeout na instalação do browser")
                    return False
                except Exception as install_error:
                    self.log(f"❌ Erro na instalação: {install_error}")
                    return False
            else:
                self.log(f"❌ Erro desconhecido do browser: {e}")
                return False

    def executar_scraping_completo(self, codigos_selecionados=None):
        """
        Executa scraping completo de todos os postos ou selecionados
        
        Args:
            codigos_selecionados: Lista de códigos (ex: ['95406', '107469']) ou None para todos
        """
        self.log("="*60)
        self.log("🚀 INICIANDO SCRAPER VIBRA ENERGIA - STANDALONE")
        self.log("="*60)
        
        # Verificar e instalar browser se necessário
        if not self.verificar_e_instalar_browser():
            self.log("❌ ERRO: Não foi possível configurar o browser")
            self.log("💡 SOLUÇÃO MANUAL:")
            self.log("   1. Abra um terminal como Administrador")
            self.log("   2. Execute: python -m playwright install chromium")
            self.log("   3. Execute o scraper novamente")
            return
        
        # Determinar quais postos processar
        if codigos_selecionados:
            postos_processar = []
            for codigo in codigos_selecionados:
                if codigo in self.todos_postos:
                    postos_processar.append(self.todos_postos[codigo])
            self.log(f"🎯 Processando {len(postos_processar)} posto(s) selecionado(s)")
        else:
            postos_processar = list(self.todos_postos.values())
            self.log(f"📋 Processando TODOS os {len(postos_processar)} postos")
        
        if not postos_processar:
            self.log("❌ Nenhum posto válido para processar")
            return
        
        # Sempre começar com Casa Caiada (posto master)
        posto_master = self.todos_postos['95406']
        if posto_master not in postos_processar:
            postos_processar.insert(0, posto_master)
        
        dados_consolidados = []
        sucessos = 0
        
        # Abrir navegador
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()
            
            try:
                for i, posto in enumerate(postos_processar):
                    self.log(f"\n{'='*60}")
                    self.log(f"🏢 POSTO {i+1}/{len(postos_processar)}: {posto['nome']}")
                    self.log(f"   Código: {posto['codigo']} | CNPJ: {posto['cnpj']}")
                    self.log(f"{'='*60}")
                    
                    try:
                        # Primeiro posto: login completo
                        if i == 0:
                            self.login(page)
                            self.navegar_pedidos(page)
                        else:
                            # Outros postos: apenas trocar
                            self.trocar_posto(page, posto['cnpj'])
                        
                        # Extrair produtos
                        produtos = self.extrair_produtos(page)
                        
                        if produtos:
                            # Preparar dados do posto
                            dados_posto = {
                                'codigo': posto['codigo'],
                                'cnpj': posto['cnpj'],
                                'razao': posto['razao'],
                                'nome': posto['nome'],
                                'produtos': produtos,
                                'data_coleta': datetime.now().strftime("%H:%M %d/%m/%Y")
                            }
                            
                            # Enviar para sistema principal
                            if self.enviar_dados_para_sistema(dados_posto):
                                sucessos += 1
                            
                            dados_consolidados.append(dados_posto)
                            
                            self.log(f"✅ Posto concluído: {len(produtos)} produtos extraídos")
                        else:
                            self.log(f"⚠️ Nenhum produto encontrado")
                        
                    except Exception as e:
                        self.log(f"❌ Erro no posto {posto['nome']}: {e}")
                        continue
                
            finally:
                browser.close()
        
        # Salvar backup local
        self.salvar_backup_local(dados_consolidados)
        
        self.log(f"\n{'='*60}")
        self.log(f"🎉 SCRAPING CONCLUÍDO!")
        self.log(f"   Postos processados: {len(postos_processar)}")
        self.log(f"   Sucessos: {sucessos}")
        self.log(f"   Dados enviados ao sistema principal: {sucessos > 0}")
        self.log(f"{'='*60}")


def main():
    """Função principal do executável"""
    print("🚀 SCRAPER VIBRA ENERGIA - EXECUTÁVEL STANDALONE")
    print("="*60)
    
    # Interface simples para seleção
    print("\nSelecione uma opção:")
    print("1. Executar TODOS os postos (11 postos)")
    print("2. Executar postos específicos")
    print("3. Executar apenas Casa Caiada (teste)")
    print("0. Sair")
    
    try:
        opcao = input("\nDigite sua opção (0-3): ").strip()
        
        if opcao == "0":
            print("👋 Saindo...")
            return
        
        elif opcao == "1":
            # Todos os postos
            scraper = VibraScraperStandalone(headless=False)  # Mostrar navegador
            scraper.executar_scraping_completo()
        
        elif opcao == "2":
            # Postos específicos
            print("\nPostos disponíveis:")
            postos_dict = {
                '95406': 'AP CASA CAIADA',
                '107469': 'POSTO ENSEADA DO NOR',
                '11236': 'POSTO REAL',
                '1153963': 'POSTO AVENIDA',
                '124282': 'R J',
                '14219': 'GLOBO105',
                '156075': 'POSTO BR SHOPPING',
                '1775869': 'POSTO DOZE',
                '5039': 'POSTO VIP',
                '61003': 'P IGARASSU',
                '94762': 'CIDADE PATRIMONIO'
            }
            
            for codigo, nome in postos_dict.items():
                print(f"  {codigo} - {nome}")
            
            codigos_input = input("\nDigite os códigos separados por espaço (ex: 95406 107469): ").strip()
            
            if codigos_input:
                codigos_selecionados = codigos_input.split()
                scraper = VibraScraperStandalone(headless=False)
                scraper.executar_scraping_completo(codigos_selecionados)
            else:
                print("❌ Nenhum código fornecido")
        
        elif opcao == "3":
            # Apenas Casa Caiada
            scraper = VibraScraperStandalone(headless=False)
            scraper.executar_scraping_completo(['95406'])
        
        else:
            print("❌ Opção inválida")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Operação cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
    
    input("\nPressione ENTER para sair...")


if __name__ == "__main__":
    main()