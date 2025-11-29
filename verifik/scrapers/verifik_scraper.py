"""
Scraper para coleta de produtos do VerifiK
Sistema similar ao Fuel Prices para coletar dados de produtos de sites externos
"""
import os
import sys
import time
import json
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae, ImagemProdutoPendente

class VerifiKScraper:
    """Scraper para coleta de produtos do VerifiK"""
    
    def __init__(self, headless=True):
        self.headless = headless
        
        # Sites de exemplo para scraping (pode ser customizado)
        self.sites_config = {
            'mercadolibre': {
                'url': 'https://lista.mercadolibre.com.br/bebidas',
                'selectors': {
                    'produto': '.ui-search-result',
                    'nome': '.ui-search-item__title',
                    'preco': '.andes-money-amount__fraction',
                    'imagem': '.ui-search-result-image__element',
                    'link': '.ui-search-link'
                }
            },
            'americanas': {
                'url': 'https://www.americanas.com.br/busca/bebidas',
                'selectors': {
                    'produto': '.product-grid-item',
                    'nome': '.product-title',
                    'preco': '.price',
                    'imagem': '.product-image img',
                    'link': '.product-link'
                }
            }
        }
    
    def log(self, message):
        """Log com timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def extrair_produtos_mercadolivre(self, page, categoria="bebidas", limite=20):
        """Extrai produtos do Mercado Livre"""
        self.log("Coletando produtos do Mercado Livre...")
        
        try:
            # Ir para página de bebidas
            url = f"https://lista.mercadolibre.com.br/{categoria}"
            page.goto(url, timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)
            time.sleep(3)
            
            # Scroll para carregar mais produtos
            for i in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
            
            # Extrair produtos
            produtos = []
            cards = page.locator('.ui-search-result').all()[:limite]
            
            for i, card in enumerate(cards, 1):
                try:
                    produto = {}
                    
                    # Nome do produto
                    try:
                        nome_element = card.locator('.ui-search-item__title')
                        if nome_element.count() > 0:
                            produto['nome'] = nome_element.first.inner_text().strip()
                    except:
                        produto['nome'] = f"Produto {i}"
                    
                    # Preço
                    try:
                        preco_element = card.locator('.andes-money-amount__fraction')
                        if preco_element.count() > 0:
                            produto['preco'] = preco_element.first.inner_text().strip()
                    except:
                        produto['preco'] = "0,00"
                    
                    # Link da imagem
                    try:
                        img_element = card.locator('img')
                        if img_element.count() > 0:
                            produto['imagem_url'] = img_element.first.get_attribute('src') or img_element.first.get_attribute('data-src')
                    except:
                        produto['imagem_url'] = None
                    
                    # Link do produto
                    try:
                        link_element = card.locator('a').first
                        if link_element.count() > 0:
                            produto['link'] = link_element.get_attribute('href')
                    except:
                        produto['link'] = None
                    
                    # Categoria
                    produto['categoria'] = categoria.upper()
                    produto['fonte'] = 'Mercado Livre'
                    produto['data_coleta'] = datetime.now().isoformat()
                    
                    if produto['nome']:
                        produtos.append(produto)
                        self.log(f"Produto {len(produtos)}: {produto['nome']}")
                
                except Exception as e:
                    self.log(f"Erro ao processar produto {i}: {e}")
                    continue
            
            self.log(f"Total de produtos coletados: {len(produtos)}")
            return produtos
            
        except Exception as e:
            self.log(f"Erro ao extrair do Mercado Livre: {e}")
            return []
    
    def baixar_imagem(self, url, nome_arquivo):
        """Baixa imagem de uma URL"""
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                # Criar diretório se não existir
                os.makedirs('media/produtos_scraping', exist_ok=True)
                
                # Salvar imagem
                caminho = f'media/produtos_scraping/{nome_arquivo}'
                with open(caminho, 'wb') as f:
                    f.write(response.content)
                
                return caminho
            
        except Exception as e:
            self.log(f"Erro ao baixar imagem {url}: {e}")
        
        return None
    
    def salvar_no_banco(self, produtos):
        """Salva produtos coletados no banco VerifiK"""
        produtos_salvos = 0
        imagens_baixadas = 0
        
        for produto in produtos:
            try:
                # Verificar se produto já existe
                nome_limpo = produto['nome'][:200]  # Limitar tamanho
                
                produto_existe = ProdutoMae.objects.filter(
                    nome__icontains=nome_limpo[:50]
                ).first()
                
                if produto_existe:
                    self.log(f"Produto já existe: {nome_limpo[:50]}...")
                    continue
                
                # Criar produto
                produto_obj = ProdutoMae.objects.create(
                    nome=nome_limpo,
                    categoria=produto.get('categoria', 'BEBIDAS'),
                    preco_referencia=self.extrair_preco(produto.get('preco', '0')),
                    origem_dados='SCRAPING',
                    url_origem=produto.get('link', ''),
                    observacoes=f"Coletado de {produto.get('fonte', 'Site Externo')} em {produto.get('data_coleta', datetime.now())}"
                )
                
                produtos_salvos += 1
                self.log(f"Produto salvo: {produto_obj.nome}")
                
                # Baixar e salvar imagem se disponível
                if produto.get('imagem_url'):
                    try:
                        # Nome do arquivo baseado no ID do produto
                        nome_arquivo = f"produto_{produto_obj.id}_{int(time.time())}.jpg"
                        caminho_imagem = self.baixar_imagem(produto['imagem_url'], nome_arquivo)
                        
                        if caminho_imagem:
                            # Criar registro de imagem pendente
                            ImagemProdutoPendente.objects.create(
                                produto=produto_obj,
                                imagem=caminho_imagem.replace('media/', ''),
                                origem='SCRAPING',
                                observacoes=f"Imagem coletada automaticamente de {produto.get('fonte', 'Site')}"
                            )
                            imagens_baixadas += 1
                            self.log(f"Imagem baixada: {nome_arquivo}")
                    
                    except Exception as e:
                        self.log(f"Erro ao processar imagem: {e}")
            
            except Exception as e:
                self.log(f"Erro ao salvar produto {produto.get('nome', 'N/A')}: {e}")
                continue
        
        self.log(f"Resumo: {produtos_salvos} produtos salvos, {imagens_baixadas} imagens baixadas")
        return produtos_salvos, imagens_baixadas
    
    def extrair_preco(self, texto_preco):
        """Extrai valor numérico do preço"""
        try:
            # Remove tudo exceto números e vírgula/ponto
            import re
            numeros = re.sub(r'[^\d,.]', '', texto_preco.replace('.', '').replace(',', '.'))
            return float(numeros) if numeros else 0.0
        except:
            return 0.0
    
    def salvar_backup(self, produtos, nome_arquivo=None):
        """Salva backup dos produtos coletados"""
        if not nome_arquivo:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"backup_verifik_scraping_{timestamp}.json"
        
        try:
            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                json.dump(produtos, f, ensure_ascii=False, indent=2)
            
            self.log(f"Backup salvo: {nome_arquivo}")
            return nome_arquivo
            
        except Exception as e:
            self.log(f"Erro ao salvar backup: {e}")
            return None
    
    def executar_coleta(self, site='mercadolibre', categoria='bebidas', limite=50):
        """Executa coleta completa de produtos"""
        self.log("="*60)
        self.log("🚀 INICIANDO SCRAPER VERIFIK")
        self.log(f"Site: {site} | Categoria: {categoria} | Limite: {limite}")
        self.log("="*60)
        
        produtos_coletados = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            try:
                if site == 'mercadolibre':
                    produtos_coletados = self.extrair_produtos_mercadolivre(page, categoria, limite)
                else:
                    self.log(f"Site '{site}' não implementado ainda")
                
                # Salvar backup
                if produtos_coletados:
                    self.salvar_backup(produtos_coletados)
                    
                    # Salvar no banco
                    produtos_salvos, imagens_baixadas = self.salvar_no_banco(produtos_coletados)
                    
                    self.log("="*60)
                    self.log("🎉 COLETA CONCLUÍDA!")
                    self.log(f"Produtos coletados: {len(produtos_coletados)}")
                    self.log(f"Produtos salvos: {produtos_salvos}")
                    self.log(f"Imagens baixadas: {imagens_baixadas}")
                    self.log("="*60)
                else:
                    self.log("❌ Nenhum produto foi coletado")
                
                # Manter navegador aberto se não for headless
                if not self.headless:
                    self.log("⏸️ Navegador aberto para conferir")
                    input("Pressione ENTER quando terminar...")
                
                return produtos_coletados
                
            except Exception as e:
                self.log(f"Erro durante coleta: {e}")
                return []
            
            finally:
                browser.close()


def main():
    """Função principal do scraper"""
    print("🚀 SCRAPER VERIFIK - COLETA DE PRODUTOS")
    print("="*60)
    
    print("\nSelecione uma opção:")
    print("1. Coletar bebidas do Mercado Livre (50 produtos)")
    print("2. Coletar bebidas do Mercado Livre (modo visual)")
    print("3. Coletar alimentos do Mercado Livre")
    print("0. Sair")
    
    try:
        opcao = input("\nDigite sua opção (0-3): ").strip()
        
        if opcao == "0":
            print("👋 Saindo...")
            return
        
        elif opcao == "1":
            # Coleta automática
            scraper = VerifiKScraper(headless=True)
            scraper.executar_coleta('mercadolibre', 'bebidas', 50)
        
        elif opcao == "2":
            # Coleta visual (mostra navegador)
            scraper = VerifiKScraper(headless=False)
            scraper.executar_coleta('mercadolibre', 'bebidas', 20)
        
        elif opcao == "3":
            # Coleta de alimentos
            scraper = VerifiKScraper(headless=True)
            scraper.executar_coleta('mercadolibre', 'alimentos', 30)
        
        else:
            print("❌ Opção inválida")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Operação cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
    
    input("\nPressione ENTER para sair...")


if __name__ == "__main__":
    main()