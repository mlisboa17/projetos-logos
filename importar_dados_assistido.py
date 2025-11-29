#!/usr/bin/env python
"""
Script para facilitar a importação de dados coletados pelo sistema standalone
"""

import os
import sys
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import json

def encontrar_pastas_exportacao():
    """Procura por pastas de exportação em locais comuns"""
    
    locais_comuns = [
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Google Drive"),
        os.path.expanduser("~/OneDrive"),
    ]
    
    pastas_encontradas = []
    
    for local in locais_comuns:
        if not os.path.exists(local):
            continue
            
        try:
            for item in os.listdir(local):
                caminho_item = os.path.join(local, item)
                if os.path.isdir(caminho_item) and item.startswith("exportacao_"):
                    # Verificar se tem a estrutura correta
                    json_file = os.path.join(caminho_item, "dados_exportacao.json")
                    if os.path.exists(json_file):
                        pastas_encontradas.append(caminho_item)
        except PermissionError:
            continue
    
    return pastas_encontradas

def mostrar_info_pasta(pasta):
    """Mostra informações sobre uma pasta de exportação"""
    
    json_file = os.path.join(pasta, "dados_exportacao.json")
    
    if not os.path.exists(json_file):
        return "❌ Pasta inválida - sem dados_exportacao.json"
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        usuario = dados.get('usuario', 'Desconhecido')
        data_exp = dados.get('data_exportacao', 'Desconhecida')
        total_imgs = len(dados.get('imagens', []))
        
        # Calcular total de anotações
        total_anotacoes = 0
        for img in dados.get('imagens', []):
            total_anotacoes += len(img.get('anotacoes', []))
        
        return f"""📊 INFORMAÇÕES DA PASTA:
├── 📁 Pasta: {os.path.basename(pasta)}
├── 👤 Usuário: {usuario}
├── 📅 Data: {data_exp[:19] if data_exp else 'N/A'}
├── 📸 Imagens: {total_imgs}
└── 📦 Anotações: {total_anotacoes}"""
        
    except Exception as e:
        return f"❌ Erro ao ler dados: {str(e)}"

def importar_pasta(pasta):
    """Executa a importação de uma pasta"""
    
    print(f"\n🚀 Iniciando importação da pasta:")
    print(f"📁 {pasta}")
    
    # Verificar se o script de importação existe
    script_importacao = "importar_dados_coletados.py"
    
    if not os.path.exists(script_importacao):
        print(f"❌ Script {script_importacao} não encontrado!")
        return False
    
    try:
        # Executar importação
        resultado = subprocess.run([
            sys.executable, 
            script_importacao, 
            pasta
        ], capture_output=True, text=True, encoding='utf-8')
        
        print(resultado.stdout)
        
        if resultado.stderr:
            print("⚠️ Avisos/Erros:")
            print(resultado.stderr)
        
        if resultado.returncode == 0:
            print("✅ Importação concluída com sucesso!")
            return True
        else:
            print(f"❌ Importação falhou (código: {resultado.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ Erro na importação: {str(e)}")
        return False

def main():
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║          IMPORTADOR DE DADOS COLETADOS - VerifiK                ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    
    # Procurar pastas automaticamente
    print("🔍 Procurando pastas de exportação...")
    pastas_encontradas = encontrar_pastas_exportacao()
    
    if pastas_encontradas:
        print(f"\n📂 Encontradas {len(pastas_encontradas)} pasta(s):")
        print()
        
        for i, pasta in enumerate(pastas_encontradas, 1):
            print(f"{i}. {mostrar_info_pasta(pasta)}")
            print(f"   📂 Caminho: {pasta}")
            print()
        
        # Perguntar qual importar
        while True:
            try:
                print("💡 Opções:")
                print("   1-N: Importar pasta específica")
                print("   A: Importar TODAS as pastas")
                print("   M: Escolher pasta manualmente")
                print("   S: Sair")
                print()
                
                escolha = input("➤ Sua escolha: ").strip().upper()
                
                if escolha == 'S':
                    print("👋 Saindo...")
                    break
                elif escolha == 'M':
                    # Escolha manual
                    root = tk.Tk()
                    root.withdraw()
                    
                    pasta_manual = filedialog.askdirectory(
                        title="Escolha a pasta de exportação",
                        initialdir=os.path.expanduser("~")
                    )
                    
                    root.destroy()
                    
                    if pasta_manual:
                        importar_pasta(pasta_manual)
                    break
                    
                elif escolha == 'A':
                    # Importar todas
                    for pasta in pastas_encontradas:
                        importar_pasta(pasta)
                    break
                    
                elif escolha.isdigit():
                    num = int(escolha)
                    if 1 <= num <= len(pastas_encontradas):
                        importar_pasta(pastas_encontradas[num-1])
                        break
                    else:
                        print("❌ Número inválido!")
                else:
                    print("❌ Opção inválida!")
                    
            except KeyboardInterrupt:
                print("\n👋 Cancelado pelo usuário")
                break
            except Exception as e:
                print(f"❌ Erro: {str(e)}")
    
    else:
        print("❌ Nenhuma pasta de exportação encontrada automaticamente.")
        print()
        print("💡 Opções:")
        print("   1. Procurar manualmente")
        print("   2. Sair")
        
        escolha = input("➤ Sua escolha (1 ou 2): ").strip()
        
        if escolha == '1':
            root = tk.Tk()
            root.withdraw()
            
            pasta_manual = filedialog.askdirectory(
                title="Escolha a pasta de exportação (ex: exportacao_20251126_143052)",
                initialdir=os.path.expanduser("~")
            )
            
            root.destroy()
            
            if pasta_manual:
                print(mostrar_info_pasta(pasta_manual))
                print()
                
                if input("➤ Importar esta pasta? (s/N): ").strip().lower() == 's':
                    importar_pasta(pasta_manual)
        else:
            print("👋 Saindo...")

if __name__ == '__main__':
    main()