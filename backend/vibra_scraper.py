"""
Web scraper para preços de combustíveis da Vibra
Login no portal: https://cn.vibraenergia.com.br/login/
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, Optional
import json
import os
from dotenv import load_dotenv

load_dotenv()


class VibraScraper:
    """
    Scraper para obter preços de combustíveis do portal Vibra (com autenticação)
    """
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        self.login_url = "https://cn.vibraenergia.com.br/login/"
        self.base_url = "https://cn.vibraenergia.com.br"
        self.username = username or os.getenv("VIBRA_USERNAME")
        self.password = password or os.getenv("VIBRA_PASSWORD")
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.is_logged_in = False
    
    def login(self) -> bool:
        """
        Faz login no portal Vibra Energia
        
        Returns:
            bool: True se login bem-sucedido, False caso contrário
        """
        if not self.username or not self.password:
            print("ERRO: Credenciais não configuradas!")
            print("Configure VIBRA_USERNAME e VIBRA_PASSWORD no arquivo .env")
            return False
        
        try:
            # 1. Acessar página de login para obter CSRF token
            print("Acessando página de login...")
            response = self.session.get(self.login_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar CSRF token (ajustar seletor conforme HTML real)
            csrf_token = None
            csrf_input = soup.find('input', {'name': 'csrf_token'}) or \
                        soup.find('input', {'name': 'csrfmiddlewaretoken'}) or \
                        soup.find('input', {'name': '_token'})
            
            if csrf_input:
                csrf_token = csrf_input.get('value')
            
            # 2. Preparar dados de login
            login_data = {
                'username': self.username,
                'password': self.password,
            }
            
            if csrf_token:
                login_data['csrf_token'] = csrf_token
            
            # 3. Enviar POST de login
            print(f"Fazendo login como {self.username}...")
            login_response = self.session.post(
                self.login_url,
                data=login_data,
                timeout=10,
                allow_redirects=True
            )
            
            # 4. Verificar se login foi bem-sucedido
            if login_response.status_code == 200:
                # Verificar se não há mensagem de erro
                if 'login' not in login_response.url.lower() or 'dashboard' in login_response.url.lower():
                    print("✓ Login realizado com sucesso!")
                    self.is_logged_in = True
                    return True
                else:
                    print("✗ Login falhou - credenciais inválidas")
                    return False
            else:
                print(f"✗ Login falhou - Status: {login_response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"✗ Erro ao fazer login: {e}")
            return False
    
    def get_fuel_prices(self, state: str = "PE") -> Dict[str, float]:
        """
        Obtém preços de combustíveis da Vibra (requer login)
        
        Args:
            state: Sigla do estado (ex: PE, SP, RJ)
            
        Returns:
            Dict com preços por tipo de combustível
        """
        # Fazer login se necessário
        if not self.is_logged_in:
            if not self.login():
                print("Usando preços MOCK (login falhou)")
                return self._get_mock_prices()
        
        try:
            # URL da página de preços (ajustar conforme estrutura real do portal)
            prices_url = f"{self.base_url}/precos" 
            
            print(f"Buscando preços em {prices_url}...")
            response = self.session.get(prices_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parsear preços do HTML
            prices = self._parse_prices(soup, state)
            
            if prices:
                print("✓ Preços obtidos com sucesso!")
                return prices
            else:
                print("⚠ Nenhum preço encontrado, usando MOCK")
                return self._get_mock_prices()
            
        except requests.RequestException as e:
            print(f"✗ Erro ao buscar preços: {e}")
            return self._get_mock_prices()
    
    def _parse_prices(self, soup: BeautifulSoup, state: str) -> Dict[str, float]:
        """
        Extrai preços do HTML do portal Vibra
        NOTA: Estrutura precisa ser ajustada após análise do HTML real
        """
        prices = {}
        
        try:
            # Buscar tabela ou cards de preços (ajustar seletores)
            price_elements = soup.find_all(class_='price') or \
                           soup.find_all(class_='fuel-price') or \
                           soup.find('table', class_='price-table')
            
            if price_elements:
                for elem in price_elements:
                    # Extrair nome do combustível e preço
                    fuel_name = elem.find(class_='fuel-name') or elem.find('td')
                    price_value = elem.find(class_='price-value') or elem.find_all('td')[1] if len(elem.find_all('td')) > 1 else None
                    
                    if fuel_name and price_value:
                        fuel_type = fuel_name.text.strip().lower()
                        price = self._extract_price(price_value.text)
                        
                        # Mapear tipos de combustível
                        if 'gasolina comum' in fuel_type or 'gasolina s' in fuel_type:
                            prices['gasolina_comum'] = price
                        elif 'gasolina aditivada' in fuel_type or 'podium' in fuel_type:
                            prices['gasolina_aditivada'] = price
                        elif 'etanol' in fuel_type or 'álcool' in fuel_type:
                            prices['etanol'] = price
                        elif 'diesel s10' in fuel_type:
                            prices['diesel_s10'] = price
                        elif 'diesel s500' in fuel_type:
                            prices['diesel_s500'] = price
            
            return prices if prices else {}
            
        except Exception as e:
            print(f"Erro ao parsear preços: {e}")
            return {}
    
    def _extract_price(self, price_text: str) -> float:
        """
        Extrai valor numérico de uma string de preço
        Exemplos: "R$ 5,89" -> 5.89
        """
        try:
            # Remover caracteres não numéricos exceto vírgula e ponto
            clean = ''.join(c for c in price_text if c.isdigit() or c in '.,')
            # Substituir vírgula por ponto
            clean = clean.replace(',', '.')
            return float(clean)
        except ValueError:
            return 0.0
    
    def _get_mock_prices(self) -> Dict[str, float]:
        """
        Retorna preços simulados para desenvolvimento/teste
        Baseados em preços reais aproximados de Recife/PE
        """
        return {
            'gasolina_comum': 5.45,
            'gasolina_aditivada': 5.72,
            'etanol': 3.89,
            'diesel_s10': 5.12,
            'diesel_s500': 4.95,
            'updated_at': datetime.now().isoformat()
        }
    
    def get_margin_analysis(
        self, 
        vibra_prices: Dict[str, float],
        postos_lisboa_prices: Dict[str, float]
    ) -> Dict[str, Dict]:
        """
        Calcula margem de lucro comparando preços de compra (Vibra) 
        com preços de venda (Postos Lisboa)
        
        Args:
            vibra_prices: Preços de compra da Vibra
            postos_lisboa_prices: Preços de venda dos Postos Lisboa
            
        Returns:
            Dict com análise de margem por combustível
        """
        analysis = {}
        
        for fuel_type in vibra_prices:
            if fuel_type == 'updated_at':
                continue
                
            if fuel_type in postos_lisboa_prices:
                compra = vibra_prices[fuel_type]
                venda = postos_lisboa_prices[fuel_type]
                
                margem_litro = venda - compra
                margem_percentual = ((venda - compra) / compra) * 100 if compra > 0 else 0
                
                # Determinar status baseado na margem
                if margem_percentual >= 15:
                    status = 'excelente'
                elif margem_percentual >= 10:
                    status = 'bom'
                elif margem_percentual >= 5:
                    status = 'atencao'
                else:
                    status = 'critico'
                
                analysis[fuel_type] = {
                    'preco_compra': round(compra, 2),
                    'preco_venda': round(venda, 2),
                    'margem_litro': round(margem_litro, 2),
                    'margem_percentual': round(margem_percentual, 2),
                    'status': status
                }
        
        return analysis
    
    def save_prices_history(self, prices: Dict, filename: str = 'prices_history.json'):
        """
        Salva histórico de preços em arquivo JSON
        """
        try:
            # Carregar histórico existente
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except FileNotFoundError:
                history = []
            
            # Adicionar novo registro
            prices['timestamp'] = datetime.now().isoformat()
            history.append(prices)
            
            # Manter apenas últimos 30 dias (1 registro por hora = 720 registros)
            if len(history) > 720:
                history = history[-720:]
            
            # Salvar
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Histórico salvo em {filename}")
                
        except Exception as e:
            print(f"✗ Erro ao salvar histórico: {e}")


# Exemplo de uso
if __name__ == "__main__":
    print("=" * 60)
    print("VIBRA SCRAPER - Análise de Preços de Combustíveis")
    print("=" * 60)
    
    # Criar scraper (credenciais do .env)
    scraper = VibraScraper()
    
    # Obter preços da Vibra
    print("\n📊 Buscando preços da Vibra...")
    print("-" * 60)
    vibra_prices = scraper.get_fuel_prices(state="PE")
    
    print("\n💰 PREÇOS DE COMPRA (VIBRA):")
    print("-" * 60)
    for fuel, price in vibra_prices.items():
        if fuel != 'updated_at':
            print(f"  {fuel.upper().replace('_', ' '):<20} R$ {price:.2f}")
    
    # Simular preços dos Postos Lisboa (depois virá do banco de dados)
    postos_prices = {
        'gasolina_comum': 5.89,
        'gasolina_aditivada': 6.15,
        'etanol': 4.29,
        'diesel_s10': 5.45,
        'diesel_s500': 5.25
    }
    
    print("\n\n💵 PREÇOS DE VENDA (POSTOS LISBOA):")
    print("-" * 60)
    for fuel, price in postos_prices.items():
        print(f"  {fuel.upper().replace('_', ' '):<20} R$ {price:.2f}")
    
    # Análise de margem
    print("\n\n📈 ANÁLISE DE MARGEM DE LUCRO:")
    print("=" * 60)
    analysis = scraper.get_margin_analysis(vibra_prices, postos_prices)
    
    for fuel, data in analysis.items():
        print(f"\n🔹 {fuel.upper().replace('_', ' ')}")
        print(f"   Compra (Vibra):    R$ {data['preco_compra']:.2f}")
        print(f"   Venda (Postos):    R$ {data['preco_venda']:.2f}")
        print(f"   Margem/Litro:      R$ {data['margem_litro']:.2f}")
        print(f"   Margem %:          {data['margem_percentual']:.1f}%")
        
        status_emoji = {
            'excelente': '🟢',
            'bom': '🟡', 
            'atencao': '🟠',
            'critico': '🔴'
        }
        print(f"   Status:            {status_emoji.get(data['status'], '⚪')} {data['status'].upper()}")
    
    # Salvar histórico
    print("\n" + "=" * 60)
    scraper.save_prices_history(vibra_prices)
    print("\n✅ Análise concluída!")
