"""
Script para importar bebidas não alcoólicas do Excel para o VerifiK

Arquivo: CadastroBebidasNaoAlcoolicas.xlsx
Total: 76 produtos
"""
import os
import sys
import django
from pathlib import Path
import pandas as pd

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae, CodigoBarrasProdutoMae

print("╔══════════════════════════════════════════════════════════════════╗")
print("║    IMPORTAÇÃO BEBIDAS NÃO ALCOÓLICAS - VERIFIK                  ║")
print("╚══════════════════════════════════════════════════════════════════╝\n")

# Ler Excel
arquivo = r'C:\Users\mlisb\Downloads\CadastroBebidasNaoAlcoolicas.xlsx'
print(f"📁 Lendo arquivo: {arquivo}")

try:
    df = pd.read_excel(arquivo)
    print(f"✅ Arquivo lido com sucesso!")
    print(f"📊 Total de produtos: {len(df)}\n")
except Exception as e:
    print(f"❌ Erro ao ler arquivo: {e}")
    exit(1)

# Estatísticas
print("="*70)
print("ESTATÍSTICAS DO ARQUIVO")
print("="*70)
print(f"Colunas encontradas: {list(df.columns)}")
print(f"Total de linhas: {len(df)}")
print(f"\nPrimeiros 3 produtos:")
print(df.head(3).to_string())
print("\n" + "="*70 + "\n")

# Confirmar importação
resposta = input("🤔 Deseja importar esses produtos para o VerifiK? (s/n): ")
if resposta.lower() != 's':
    print("❌ Importação cancelada.")
    exit(0)

# Importar produtos
print("\n🚀 Iniciando importação...\n")

produtos_criados = 0
produtos_atualizados = 0
codigos_adicionados = 0
erros = 0

for idx, row in df.iterrows():
    try:
        codigo_barras = str(row['Código']).strip()
        descricao = str(row['Descrição']).strip()
        categoria = str(row['CATEGORIA']).strip()
        preco = float(row['Preço Venda'])
        
        # Extrair marca da descrição (primeira palavra geralmente)
        palavras = descricao.split()
        marca = palavras[0] if palavras else 'Genérica'
        
        # Verificar se produto já existe (por descrição similar)
        produto_existente = ProdutoMae.objects.filter(
            descricao_produto__iexact=descricao
        ).first()
        
        if produto_existente:
            produto = produto_existente
            # Atualizar preço se mudou
            if produto.preco != preco:
                produto.preco = preco
                produto.save()
            print(f"  ⚠️  [{idx+1:3d}/{len(df)}] Produto já existe: {descricao[:50]}")
            produtos_atualizados += 1
        else:
            # Criar novo produto
            produto = ProdutoMae.objects.create(
                descricao_produto=descricao,
                marca=marca,
                tipo=categoria,  # Usa categoria do Excel
                preco=preco,
                ativo=True
            )
            print(f"  ✅ [{idx+1:3d}/{len(df)}] Criado: {descricao[:50]}")
            produtos_criados += 1
        
        # Adicionar código de barras (se não existir)
        codigo_existente = CodigoBarrasProdutoMae.objects.filter(
            codigo=codigo_barras
        ).first()
        
        if not codigo_existente:
            CodigoBarrasProdutoMae.objects.create(
                produto_mae=produto,  # Campo correto: produto_mae
                codigo=codigo_barras,
                principal=True
            )
            codigos_adicionados += 1
            print(f"       📊 Código de barras adicionado: {codigo_barras}")
        else:
            print(f"       ⚠️  Código de barras já existe: {codigo_barras}")
        
    except Exception as e:
        erros += 1
        print(f"  ❌ [{idx+1:3d}/{len(df)}] ERRO: {descricao[:50]}")
        print(f"       Motivo: {e}")

# Relatório final
print("\n" + "="*70)
print("RELATÓRIO FINAL")
print("="*70)
print(f"✅ Produtos criados:       {produtos_criados}")
print(f"⚠️  Produtos atualizados:   {produtos_atualizados}")
print(f"📊 Códigos adicionados:    {codigos_adicionados}")
print(f"❌ Erros:                  {erros}")
print(f"📦 Total processado:       {len(df)}")
print("="*70)

# Verificar total no banco
total_banco = ProdutoMae.objects.count()
total_codigos = CodigoBarrasProdutoMae.objects.count()

print(f"\n📊 BANCO DE DADOS ATUAL:")
print(f"   • Total de produtos: {total_banco}")
print(f"   • Total de códigos: {total_codigos}")

print("\n✅ Importação concluída!")
print("\n💡 Próximos passos:")
print("   1. Acessar: http://localhost:8000/admin/verifik/produtomae/")
print("   2. Verificar produtos importados")
print("   3. Adicionar imagens para treinar IA")
print("   4. Treinar modelo YOLO com os produtos")
