#!/usr/bin/env python3
"""
SCRAPER VIBRA ENERGIA - VERSÃO SIMPLIFICADA SEM PLAYWRIGHT
Sistema que simula dados ou usa web scraping simples
"""

import os
import sys
import time
import json
import requests
from datetime import datetime

class VibraScraperSimples:
    """Scraper simplificado que funciona sem browser"""
    
    def __init__(self, api_url="http://127.0.0.1:8000/fuel/api"):
        self.api_url = api_url
        
        # Lista dos 11 postos do Grupo Lisboa
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
        
        # Produtos típicos com preços simulados (baseados em dados reais)
        self.produtos_base = [
            {'nome': 'ETANOL COMUM', 'preco_base': 3.65, 'variacao': 0.15},
            {'nome': 'GASOLINA COMUM', 'preco_base': 5.89, 'variacao': 0.20},
            {'nome': 'GASOLINA ADITIVADA', 'preco_base': 6.05, 'variacao': 0.18},
            {'nome': 'DIESEL COMUM', 'preco_base': 5.45, 'variacao': 0.25},
            {'nome': 'DIESEL S10', 'preco_base': 5.52, 'variacao': 0.22},
            {'nome': 'ARLA 32', 'preco_base': 3.20, 'variacao': 0.10},
        ]
    
    def log(self, message):
        """Log com timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def verificar_sistema_principal(self):
        """Verifica se o sistema principal está funcionando"""
        try:
            response = requests.get(f"{self.api_url}/status/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log(f"[OK] Sistema principal online: {data['sistema']}")
                return True
            else:
                self.log(f"[ERRO] Sistema retornou HTTP {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.log("[ERRO] Sistema principal nao esta rodando")
            self.log("[DICA] Execute: python manage.py runserver")
            return False
        except Exception as e:
            self.log(f"[ERRO] Erro de conexao: {e}")
            return False
    
    def gerar_precos_simulados(self, posto_codigo):
        """
        Gera preços simulados baseados em dados reais
        Cada posto tem pequenas variações nos preços
        """
        import random
        
        produtos = []
        
        # Seed baseado no código do posto para consistência
        random.seed(int(posto_codigo))
        
        for produto_base in self.produtos_base:
            # Calcular variação aleatória mas consistente para o posto
            variacao = random.uniform(-produto_base['variacao'], produto_base['variacao'])
            preco_final = produto_base['preco_base'] + variacao
            
            produto = {
                'nome': produto_base['nome'],
                'preco': f"Preço: R$ {preco_final:.4f}",
                'prazo': '3 Dias',  # PADRONIZADO PARA 3 DIAS
                'base': random.choice(['Base Suape', 'Base Recife', 'Base Ipojuca'])
            }
            
            produtos.append(produto)
        
        return produtos
    
    def enviar_dados_para_sistema(self, dados_posto):
        """Envia dados para o sistema principal"""
        try:
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
            
            response = requests.post(
                f"{self.api_url}/scraper-data/",
                json=payload,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"[OK] Dados enviados: {result['detalhes']['precos_salvos']} precos")
                return True
            else:
                self.log(f"[ERRO] Erro HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"[ERRO] Erro ao enviar: {e}")
            return False
    
    def salvar_backup_local(self, dados_consolidados):
        """Salva backup local dos dados"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_scraper_simples_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(dados_consolidados, f, ensure_ascii=False, indent=2)
            
            self.log(f"[BACKUP] Backup salvo: {filename}")
            return filename
            
        except Exception as e:
            self.log(f"[ERRO] Erro ao salvar backup: {e}")
            return None
    
    def executar_coleta_simulada(self, codigos_selecionados=None):
        """
        Executa coleta simulada de preços
        NOTA: Esta versão gera dados simulados baseados em preços reais
        Para dados reais do portal Vibra, use a versão com Playwright
        """
        self.log("="*60)
        self.log("SCRAPER VIBRA - VERSAO SIMPLIFICADA")
        self.log("MODO SIMULADO: Dados baseados em precos reais")
        self.log("="*60)
        
        # Verificar sistema principal
        if not self.verificar_sistema_principal():
            self.log("[ERRO] Sistema principal indisponivel")
            return
        
        # Determinar postos a processar
        if codigos_selecionados:
            postos_processar = []
            for codigo in codigos_selecionados:
                if codigo in self.todos_postos:
                    postos_processar.append(self.todos_postos[codigo])
            self.log(f"🎯 Processando {len(postos_processar)} posto(s) selecionado(s)")
        else:
            postos_processar = list(self.todos_postos.values())
            self.log(f"[INFO] Processando TODOS os {len(postos_processar)} postos")
        
        dados_consolidados = []
        sucessos = 0
        
        for i, posto in enumerate(postos_processar, 1):
            self.log(f"\n{'='*60}")
            self.log(f"[POSTO] {i}/{len(postos_processar)}: {posto['nome']}")
            self.log(f"   Código: {posto['codigo']} | CNPJ: {posto['cnpj']}")
            
            try:
                # Simular delay de processamento
                time.sleep(1)
                
                # Gerar preços simulados
                produtos = self.gerar_precos_simulados(posto['codigo'])
                
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
                self.log(f"[OK] Posto concluido: {len(produtos)} produtos")
                
            except Exception as e:
                self.log(f"[ERRO] Erro no posto {posto['nome']}: {e}")
                continue
        
        # Salvar backup
        self.salvar_backup_local(dados_consolidados)
        
        self.log(f"\n{'='*60}")
        self.log(f"🎉 COLETA CONCLUÍDA!")
        self.log(f"   Postos processados: {len(postos_processar)}")
        self.log(f"   Sucessos: {sucessos}")
        self.log(f"   Modo: SIMULADO (baseado em dados reais)")
        self.log(f"{'='*60}")


def main():
    """Função principal"""
    print("SCRAPER VIBRA ENERGIA - VERSAO SIMPLIFICADA")
    print("="*60)
    print("MODO SIMULADO: Gera dados baseados em precos reais")
    print("Para dados reais do portal, use a versao completa")
    print("="*60)
    
    print("\nSelecione uma opcao:")
    print("1. Executar TODOS os postos (11 postos)")
    print("2. Executar postos especificos")
    print("3. Executar apenas Casa Caiada (teste)")
    print("0. Sair")
    
    try:
        opcao = input("\nDigite sua opcao (0-3): ").strip()
        
        if opcao == "0":
            print("Saindo...")
            return
        
        scraper = VibraScraperSimples()
        
        if opcao == "1":
            # Todos os postos
            scraper.executar_coleta_simulada()
        
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
            
            codigos_input = input("\nDigite os códigos separados por espaço: ").strip()
            
            if codigos_input:
                codigos_selecionados = codigos_input.split()
                scraper.executar_coleta_simulada(codigos_selecionados)
            else:
                print("[ERRO] Nenhum codigo fornecido")
        
        elif opcao == "3":
            # Apenas Casa Caiada
            scraper.executar_coleta_simulada(['95406'])
        
        else:
            print("[ERRO] Opcao invalida")
    
    except KeyboardInterrupt:
        print("\n\n[AVISO] Operacao cancelada pelo usuario")
    except Exception as e:
        print(f"\n[ERRO] Erro: {e}")
    
    input("\nPressione ENTER para sair...")


if __name__ == "__main__":
    main()