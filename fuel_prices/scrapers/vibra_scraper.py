"""
Scraper para portal Vibra Energia
Extrai preços de combustíveis dos postos
"""
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


class VibraScraper:
    """Scraper do portal Vibra Energia"""
    
    def __init__(self, username: str, password: str, headless: bool = False):
        """
        Args:
            username: Login do portal Vibra
            password: Senha do portal Vibra
            headless: Se True, roda sem abrir navegador visível
        """
        self.username = username
        self.password = password
        self.headless = headless
        self.login_url = "https://cn.vibraenergia.com.br/login/"
        
    def close_popups(self, page, max_attempts=15):
        """
        Fecha todos os popups/banners que aparecem após login
        Baseado exatamente no código gerado pelo Playwright Codegen
        """
        print("🔍 Fechando modais...")
        
        modals_fechados = 0
        
        # Tentar múltiplas vezes pois modais aparecem em sequência
        for attempt in range(max_attempts):
            modal_encontrado = False
            
            try:
                # Procurar botão "Continuar" diretamente (mais simples)
                continuar = page.get_by_role("button", name="Continuar")
                if continuar.count() > 0:
                    # Verificar se está visível
                    if continuar.first.is_visible(timeout=1000):
                        print(f"  ✓ Modal {modals_fechados + 1} - Botão Continuar encontrado")
                        continuar.first.click()
                        modals_fechados += 1
                        time.sleep(2)  # Aguardar modal fechar/trocar
                        modal_encontrado = True
                        print(f"  ✓ Modal {modals_fechados} fechado")
                        continue
            except Exception as e:
                pass
            
            try:
                # Tentar clicar em checkbox se houver (antes de Continuar)
                checkbox = page.locator('input[name*="j_idt"]')
                if checkbox.count() > 0 and checkbox.first.is_visible(timeout=500):
                    print(f"  ℹ️ Checkbox encontrado, clicando...")
                    checkbox.first.click()
                    time.sleep(0.5)
                    # Depois clicar em Continuar
                    continuar2 = page.get_by_role("button", name="Continuar")
                    if continuar2.count() > 0 and continuar2.first.is_visible(timeout=500):
                        continuar2.first.click()
                        modals_fechados += 1
                        time.sleep(2)
                        modal_encontrado = True
                        print(f"  ✓ Modal {modals_fechados} fechado (com checkbox)")
            except:
                pass
            
            # Pressionar ESC como fallback
            try:
                page.keyboard.press('Escape')
                time.sleep(0.3)
            except:
                pass
            
            # Se não encontrou modal, contar tentativas vazias
            if not modal_encontrado:
                if attempt >= 3:  # Parar após 3 tentativas sem achar nada
                    break
        
        print(f"✓ {modals_fechados} modal(is) fechado(s)")

    
    def login(self, page):
        """Faz login no portal"""
        print(f"🔐 Fazendo login com usuário {self.username}...")
        
        # Ir para página de login
        page.goto(self.login_url)
        page.wait_for_load_state('networkidle')
        time.sleep(1)  # Aguardar carregar
        
        # Preencher campo de usuário (tentar vários seletores)
        user_selectors = [
            'input[name="usuario"]',
            'input[name="username"]',
            'input[name="user"]',
            'input[name="login"]',
            'input[type="text"]',
            'input#username',
            'input#user',
            'input#login'
        ]
        
        user_filled = False
        for selector in user_selectors:
            try:
                if page.locator(selector).is_visible(timeout=2000):
                    page.fill(selector, self.username)
                    print(f"  ✓ Campo usuário encontrado: {selector}")
                    user_filled = True
                    break
            except:
                continue
        
        if not user_filled:
            raise Exception("Campo de usuário não encontrado")
        
        time.sleep(0.3)
        
        # Preencher campo de senha (tentar vários seletores)
        pass_selectors = [
            'input[name="senha"]',
            'input[name="password"]',
            'input[type="password"]',
            'input#password',
            'input#senha'
        ]
        
        pass_filled = False
        for selector in pass_selectors:
            try:
                if page.locator(selector).is_visible(timeout=2000):
                    page.fill(selector, self.password)
                    print(f"  ✓ Campo senha encontrado: {selector}")
                    pass_filled = True
                    break
            except:
                continue
        
        if not pass_filled:
            raise Exception("Campo de senha não encontrado")
        
        time.sleep(0.3)
        
        # Clicar em botão de entrar (tentar vários seletores)
        button_selectors = [
            'button[type="submit"]',
            'button:has-text("Entrar")',
            'button:has-text("Login")',
            'button:has-text("Acessar")',
            'input[type="submit"]',
            'button.btn-primary',
            'button.submit'
        ]
        
        button_clicked = False
        for selector in button_selectors:
            try:
                if page.locator(selector).is_visible(timeout=2000):
                    page.click(selector)
                    print(f"  ✓ Botão login encontrado: {selector}")
                    button_clicked = True
                    break
            except:
                continue
        
        if not button_clicked:
            # Tentar pressionar Enter no campo de senha
            print("  ⚠️ Botão não encontrado, tentando Enter...")
            page.press(pass_selectors[0], 'Enter')
        
        # Aguardar redirecionamento (usar timeout maior)
        try:
            page.wait_for_load_state('networkidle', timeout=60000)  # 60 segundos
        except:
            print("  ⚠️ Timeout na networkidle, mas continuando...")
            pass
        
        time.sleep(2)  # Aguardar popups carregarem
        
        # Fechar popups que aparecem após login (múltiplas tentativas)
        # Às vezes aparecem 3 ou 4 modais sequenciais
        # IMPORTANTE: Precisa fechar TODOS antes de acessar o menu
        print("\n🎯 Fechando TODOS os modais antes de navegar...")
        self.close_popups(page, max_attempts=25)  # 25 tentativas
        
        # Aguardar um pouco mais para garantir que não apareça outro modal
        time.sleep(2)
        
        # Verificação final de modais
        print("🔍 Verificação final de modais...")
        self.close_popups(page, max_attempts=10)  # 10 tentativas extras
        
        print("✓ Login realizado com sucesso - Todos os modais fechados")
    
    def trocar_posto(self, page, nome_posto=None):
        """Troca o posto selecionado no dropdown"""
        print(f"\n🏢 Trocando posto: {nome_posto or 'próximo'}...")
        try:
            # Clicar no dropdown de posto
            # TODO: Você precisa me passar o seletor do Codegen para o dropdown de postos
            # Por enquanto, deixando preparado
            time.sleep(1)
            print("  ✓ Posto trocado")
        except Exception as e:
            print(f"  ⚠️ Erro ao trocar posto: {e}")
            raise
    
    def navegar_pedidos(self, page):
        """Navega para seção de Pedidos usando seletor exato do Codegen"""
        print("\n🛒 Navegando para Pedidos...")
        
        # NÃO fechar modais aqui - já foram fechados no login
        time.sleep(1)
        
        try:
            # Usar seletor exato do Codegen
            pedidos_btn = page.get_by_role("button", name="Pedidos")
            
            if pedidos_btn.count() > 0 and pedidos_btn.first.is_visible(timeout=5000):
                print("  ✓ Botão Pedidos encontrado")
                pedidos_btn.first.click()
            else:
                # Fallback: tentar outros seletores
                print("  ⚠️ Botão Pedidos não visível, tentando alternativas...")
                time.sleep(1)
                
                # Tentar novamente
                if pedidos_btn.count() > 0:
                    pedidos_btn.first.click()
                else:
                    # Última tentativa: link com texto
                    page.locator('a:has-text("Pedidos")').first.click()
                
        except Exception as e:
            print(f"  ⚠️ Erro ao navegar: {e}")
            raise
        
        # Aguardar carregamento
        try:
            page.wait_for_load_state('networkidle', timeout=60000)
        except:
            print("  ⚠️ Timeout na networkidle, continuando...")
            pass
        
        time.sleep(1.5)
        
        # NÃO fechar modais aqui - já foram fechados no login
        
        print("✓ Página de Pedidos carregada")
        
        # SELECIONAR MODALIDADE FOB
        print("\n📦 Selecionando modalidade FOB...")
        try:
            # Clicar no dropdown de modalidade (usando seletor do Codegen)
            modalidade_dropdown = page.get_by_text("Modalidade", exact=False).first
            if modalidade_dropdown.is_visible(timeout=3000):
                modalidade_dropdown.click()
                time.sleep(0.5)
                
                # Clicar na opção FOB
                fob_option = page.locator("#mat-option-3").get_by_text("FOB")
                if fob_option.is_visible(timeout=2000):
                    fob_option.first.click()
                    print("  ✓ Modalidade FOB selecionada")
                    time.sleep(1)  # Aguardar atualizar produtos
                else:
                    # Tentar alternativa
                    page.get_by_text("FOB", exact=True).first.click()
                    print("  ✓ Modalidade FOB selecionada (alternativa)")
                    time.sleep(1)
            else:
                print("  ⚠️ Dropdown de modalidade não encontrado")
        except Exception as e:
            print(f"  ⚠️ Erro ao selecionar modalidade: {e}")
            print("  ⚠️ Continuando sem selecionar modalidade...")
    
    def scroll_to_load_all(self, page):
        """Faz scroll down para carregar todos os produtos"""
        print("  📜 Fazendo scroll para carregar todos os produtos...")
        
        # Pegar altura inicial
        last_height = page.evaluate("document.body.scrollHeight")
        
        while True:
            # Scroll até o final
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1.5)  # Aguardar carregar
            
            # Calcular nova altura
            new_height = page.evaluate("document.body.scrollHeight")
            
            # Se não mudou, já carregou tudo
            if new_height == last_height:
                break
            
            last_height = new_height
        
        # Voltar ao topo
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.5)  # Aguardar scroll
        print("  ✓ Todos os produtos carregados")
    
    def extrair_produtos_pedidos(self, page):
        """
        Extrai informações dos produtos da página de Pedidos
        Retorna: dict com nome_posto, modalidade e lista de produtos
        """
        print("\n📦 EXTRAINDO PRODUTOS...")
        
        # 1. Extrair nome do posto (topo da página)
        try:
            # Tentar diferentes seletores para o nome do posto
            nome_posto = None
            possveis_seletores = [
                'header h1',
                'header .posto',
                '[class*="posto"]',
                '.header-title',
                'h1'
            ]
            
            for seletor in possveis_seletores:
                try:
                    elemento = page.locator(seletor).first
                    if elemento.is_visible(timeout=1000):
                        texto = elemento.inner_text().strip()
                        if texto and len(texto) > 5:  # Validar que não é vazio
                            nome_posto = texto
                            break
                except:
                    continue
            
            if not nome_posto:
                # Tentar pegar do cabeçalho completo
                header = page.locator('header').first
                nome_posto = header.inner_text().split('\n')[0].strip()
            
            print(f"  🏢 Posto: {nome_posto}")
        except Exception as e:
            nome_posto = "Não identificado"
            print(f"  ⚠️ Não foi possível identificar o posto: {e}")
        
        # 2. Extrair modalidade (usando seletor do Codegen)
        try:
            # Tentar pegar o texto que contém "Modalidade"
            modalidade_element = page.get_by_text("Modalidade", exact=False).first
            if modalidade_element.is_visible(timeout=2000):
                # Pegar o texto completo que pode ser "FOBModalidade" ou similar
                texto_modalidade = modalidade_element.inner_text()
                # Extrair apenas a modalidade (FOB, CIF, etc)
                modalidade = texto_modalidade.replace("Modalidade", "").strip()
            else:
                modalidade = None
            
            # Se não encontrou, tentar alternativas
            if not modalidade:
                # Tentar pegar do select/dropdown
                try:
                    select_modalidade = page.locator('mat-select').first
                    if select_modalidade.is_visible(timeout=1000):
                        modalidade = select_modalidade.inner_text().strip()
                except:
                    pass
            
            print(f"  📋 Modalidade: {modalidade or 'Não identificada'}")
        except Exception as e:
            print(f"  ⚠️ Erro ao extrair modalidade: {e}")
            modalidade = None
        
        # 3. Scroll para carregar todos os produtos
        self.scroll_to_load_all(page)
        
        # 4. Extrair cards de produtos
        produtos = []
        
        # Usar seletor correto do Codegen: app-item-vitrine
        try:
            cards = page.locator("app-item-vitrine").all()
            print(f"  ✓ Encontrados {len(cards)} produtos")
        except:
            print("  ⚠️ Nenhum produto encontrado")
            return {
                'posto': nome_posto,
                'modalidade': modalidade,
                'produtos': [],
                'data_coleta': datetime.now().isoformat()
            }
        
        if not cards or len(cards) == 0:
            print("  ⚠️ Nenhum card encontrado")
            return {
                'posto': nome_posto,
                'modalidade': modalidade,
                'produtos': [],
                'data_coleta': datetime.now().isoformat()
            }
        
        # 5. Processar cada card
        print(f"  🔍 Processando {len(cards)} produtos...")
        
        # Dicionário para evitar duplicatas (chave: nome do produto)
        produtos_unicos = {}
        
        for i, card in enumerate(cards, 1):
            try:
                # Extrair informações do card usando seletores do Codegen
                produto_info = {
                    'nome': None,
                    'base': None,
                    'preco': None,
                    'prazo': None
                }
                
                # Pegar todo o texto do card
                texto_card = card.inner_text()
                
                # DEBUG: Mostrar conteúdo
                print(f"\n    📦 Card {i}:")
                print(f"    Texto: {texto_card[:150]}")
                
                # Verificar se está indisponível
                if 'indisponível' in texto_card.lower() or 'indisponivel' in texto_card.lower():
                    print(f"    ⚠️ Indisponível - pulando")
                    continue
                
                # Extrair dados linha por linha
                linhas = [l.strip() for l in texto_card.split('\n') if l.strip()]
                
                for idx, linha in enumerate(linhas):
                    linha_lower = linha.lower()
                    
                    # Nome do produto (primeira linha ou linha com nome do combustível)
                    if not produto_info['nome']:
                        if any(comb in linha_lower for comb in ['etanol', 'gasolina', 'diesel', 'arla', 'gnv']):
                            produto_info['nome'] = linha
                        elif idx == 0 and linha_lower not in ['disponível', 'em estoque']:
                            produto_info['nome'] = linha
                    
                    # Preço (contém "R$" ou "Preço:")
                    if 'r$' in linha_lower or 'preço:' in linha_lower or 'preco:' in linha_lower:
                        if not produto_info['preco']:
                            produto_info['preco'] = linha
                    
                    # Prazo (contém "dia" ou "prazo")
                    if 'dia' in linha_lower and 'prazo' not in linha_lower:
                        if not produto_info['prazo']:
                            produto_info['prazo'] = linha
                    
                    # Base (contém "base")
                    if 'base' in linha_lower:
                        produto_info['base'] = linha
                
                # Se conseguiu extrair pelo menos nome, verificar se já existe
                if produto_info['nome']:
                    # Usar nome como chave para evitar duplicatas
                    if produto_info['nome'] not in produtos_unicos:
                        produtos_unicos[produto_info['nome']] = produto_info
                        print(f"    ✓ {produto_info['nome']}")
                        if produto_info['preco']:
                            print(f"      💰 {produto_info['preco']}")
                        if produto_info['prazo']:
                            print(f"      ⏱️ {produto_info['prazo']}")
                    else:
                        print(f"    ⚠️ Duplicado - ignorando")
                else:
                    print(f"    ⚠️ Não conseguiu extrair nome do produto")
                
            except Exception as e:
                print(f"    ❌ Erro ao processar card {i}: {e}")
                continue
        
        # Converter dicionário de volta para lista
        produtos = list(produtos_unicos.values())
        
        print(f"\n  ✅ Total extraído: {len(produtos)} produtos disponíveis")
        
        # Formatar data/hora: HH:MM dd/mm/AAAA
        agora = datetime.now()
        data_hora_formatada = agora.strftime("%H:%M %d/%m/%Y")
        
        return {
            'posto': nome_posto,
            'modalidade': modalidade,
            'produtos': produtos,
            'data_coleta': data_hora_formatada
        }
    
    def take_screenshot(self, page, filename='vibra_screenshot.png'):
        """Tira screenshot da tela atual"""
        page.screenshot(path=filename, full_page=True)
        print(f"📸 Screenshot salvo: {filename}")
    
    def run_scraping(self, output_file='vibra_precos.json'):
        """
        Executa scraping completo do portal
        Extrai preços de todos os produtos disponíveis
        """
        with sync_playwright() as p:
            # Iniciar navegador
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()
            
            try:
                # Fazer login
                self.login(page)
                
                # Navegar para Pedidos
                self.navegar_pedidos(page)
                
                # Extrair produtos
                dados = self.extrair_produtos_pedidos(page)
                
                # Salvar em JSON
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(dados, f, ensure_ascii=False, indent=2)
                
                print(f"\n💾 Dados salvos em: {output_file}")
                print(f"📊 Resumo:")
                print(f"   Posto: {dados['posto']}")
                print(f"   Modalidade: {dados['modalidade']}")
                print(f"   Produtos extraídos: {len(dados['produtos'])}")
                
                # Tirar screenshot final
                self.take_screenshot(page, 'vibra_final.png')
                
                # Manter navegador aberto se não for headless
                if not self.headless:
                    print("\n⏸️  Navegador aberto para conferir")
                    print("   Pressione ENTER quando terminar...")
                    input()
                
                return dados
                
            except Exception as e:
                print(f"\n❌ Erro: {e}")
                self.take_screenshot(page, 'vibra_erro.png')
                raise
            
            finally:
                browser.close()


def main():
    """Função principal para teste"""
    # Credenciais do Grupo Lisboa
    scraper = VibraScraper(
        username='95406',
        password='Apcc2350',
        headless=False  # Mudar para True quando quiser rodar sem ver navegador
    )
    
    # Executar scraping
    dados = scraper.run_scraping('vibra_precos.json')
    
    print("\n" + "="*60)
    print("✅ SCRAPING CONCLUÍDO!")
    print("="*60)


if __name__ == '__main__':
    main()

