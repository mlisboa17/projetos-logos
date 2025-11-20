"""
WebPostos ERP Integration
Conector para integração com o sistema WebPostos usado pelos Postos Lisboa
"""
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WebPostosConnector:
    """
    Conector para API do WebPostos
    
    Funcionalidades:
    - Autenticação
    - Consulta de vendas
    - Consulta de estoque (tanques)
    - Consulta de preços
    - Relatórios financeiros
    """
    
    def __init__(
        self,
        api_url: str,
        username: str,
        password: str,
        api_key: Optional[str] = None
    ):
        self.api_url = api_url.rstrip('/')
        self.username = username
        self.password = password
        self.api_key = api_key
        self.session = requests.Session()
        self.token = None
        
    def authenticate(self) -> bool:
        """
        Autenticar no WebPostos e obter token
        
        Returns:
            bool: True se autenticação bem-sucedida
        """
        try:
            endpoint = f"{self.api_url}/auth/login"
            
            payload = {
                "username": self.username,
                "password": self.password
            }
            
            if self.api_key:
                payload["api_key"] = self.api_key
            
            response = self.session.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.token = data.get("access_token") or data.get("token")
            
            if self.token:
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                logger.info("✅ Autenticação WebPostos bem-sucedida")
                return True
            
            return False
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro na autenticação WebPostos: {e}")
            return False
    
    def get_sales(
        self,
        store_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Buscar vendas do período
        
        Args:
            store_id: ID da loja/posto (opcional)
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
            
        Returns:
            Lista de vendas
        """
        try:
            endpoint = f"{self.api_url}/sales"
            
            params = {}
            if store_id:
                params["store_id"] = store_id
            if start_date:
                params["start_date"] = start_date.isoformat()
            if end_date:
                params["end_date"] = end_date.isoformat()
            
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get("sales", [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao buscar vendas: {e}")
            return []
    
    def get_fuel_stock(self, store_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Buscar níveis dos tanques de combustível
        
        Args:
            store_id: ID da loja/posto (opcional)
            
        Returns:
            Lista com níveis dos tanques
        """
        try:
            endpoint = f"{self.api_url}/fuel/stock"
            
            params = {}
            if store_id:
                params["store_id"] = store_id
            
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get("tanks", [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao buscar estoque: {e}")
            return []
    
    def get_fuel_prices(self, store_id: Optional[int] = None) -> Dict[str, float]:
        """
        Buscar preços dos combustíveis
        
        Args:
            store_id: ID da loja/posto (opcional)
            
        Returns:
            Dicionário com preços {combustivel: preco}
        """
        try:
            endpoint = f"{self.api_url}/fuel/prices"
            
            params = {}
            if store_id:
                params["store_id"] = store_id
            
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get("prices", {})
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao buscar preços: {e}")
            return {}
    
    def update_fuel_prices(
        self,
        store_id: int,
        prices: Dict[str, float]
    ) -> bool:
        """
        Atualizar preços dos combustíveis
        
        Args:
            store_id: ID da loja/posto
            prices: Dicionário com preços {combustivel: preco}
            
        Returns:
            bool: True se atualização bem-sucedida
        """
        try:
            endpoint = f"{self.api_url}/fuel/prices"
            
            payload = {
                "store_id": store_id,
                "prices": prices
            }
            
            response = self.session.put(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            
            logger.info(f"✅ Preços atualizados para loja {store_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao atualizar preços: {e}")
            return False
    
    def get_financial_summary(
        self,
        store_id: Optional[int] = None,
        period: str = "today"
    ) -> Dict[str, Any]:
        """
        Buscar resumo financeiro
        
        Args:
            store_id: ID da loja/posto (opcional)
            period: Período (today, week, month, year)
            
        Returns:
            Dicionário com resumo financeiro
        """
        try:
            endpoint = f"{self.api_url}/financial/summary"
            
            params = {"period": period}
            if store_id:
                params["store_id"] = store_id
            
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao buscar resumo financeiro: {e}")
            return {}
    
    def get_employees(self, store_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Buscar lista de funcionários
        
        Args:
            store_id: ID da loja/posto (opcional)
            
        Returns:
            Lista de funcionários
        """
        try:
            endpoint = f"{self.api_url}/employees"
            
            params = {}
            if store_id:
                params["store_id"] = store_id
            
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get("employees", [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao buscar funcionários: {e}")
            return []
    
    def sync_all_data(self, store_id: int) -> Dict[str, Any]:
        """
        Sincronizar todos os dados de uma loja
        
        Args:
            store_id: ID da loja/posto
            
        Returns:
            Dicionário com todos os dados sincronizados
        """
        logger.info(f"🔄 Iniciando sincronização completa - Loja {store_id}")
        
        if not self.token:
            if not self.authenticate():
                return {"error": "Falha na autenticação"}
        
        data = {
            "store_id": store_id,
            "timestamp": datetime.utcnow().isoformat(),
            "sales": self.get_sales(store_id),
            "fuel_stock": self.get_fuel_stock(store_id),
            "fuel_prices": self.get_fuel_prices(store_id),
            "financial": self.get_financial_summary(store_id),
            "employees": self.get_employees(store_id)
        }
        
        logger.info(f"✅ Sincronização completa finalizada - Loja {store_id}")
        return data


# Exemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Conectar ao WebPostos
    connector = WebPostosConnector(
        api_url="https://api.webpostos.com.br",  # URL fictícia
        username="postos.lisboa",
        password="senha_exemplo",
        api_key="key_exemplo"
    )
    
    # Autenticar
    if connector.authenticate():
        print("✅ Conectado ao WebPostos")
        
        # Buscar dados
        sales = connector.get_sales(store_id=1)
        print(f"📊 Vendas: {len(sales)} registros")
        
        prices = connector.get_fuel_prices(store_id=1)
        print(f"💰 Preços: {prices}")
        
        stock = connector.get_fuel_stock(store_id=1)
        print(f"⛽ Estoque: {len(stock)} tanques")
    else:
        print("❌ Erro na autenticação")
