"""
Importa os preços do Vibra dos arquivos JSON para o banco de dados Django
Resolve o problema de "async context" do Playwright
"""
import os
import sys
import django
import json
from pathlib import Path
from datetime import datetime

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from fuel_prices.models import PostoVibra, PrecoVibra
from django.utils import timezone


def importar_json_individual(dados):
    """
    Importa dados de um posto a partir de um dicionário JSON
    
    Args:
        dados: Dicionário com dados do posto (da lista do arquivo consolidado)
        
    Returns:
        Tupla (posto_nome, precos_salvos)
    """
    
    # Extrair informações do posto
    codigo_vibra = dados.get('codigo_vibra', '')
    razao_social = dados.get('razao_social', '')
    cnpj = dados.get('cnpj', '')
    nome_posto_original = dados.get('posto', '')
    
    if not cnpj:
        codigo = dados.get('codigo_vibra', 'DESCONHECIDO')
        print(f"  [SKIP] Posto sem CNPJ: {codigo}")
        return (None, 0)
    
    # CRIAR NOME AMIGÁVEL baseado na razão social
    # Mapeamento de nomes conhecidos (CURTOS para caber na tela)
    nomes_amigaveis = {
        '04284939000186': 'Casa Caiada',
        '00338804000103': 'Enseada',
        '24156978000105': 'Real',
        '05428059000280': 'Avenida',
        '08726064000186': 'R.J.',
        '41043647000188': 'Globo',
        '07018760000175': 'BR Shopping',
        '52308604000101': 'Doze',
        '03008754000186': 'VIP',
        '04274378000134': 'Igarassu',
        '05428059000107': 'Patrimônio',
    }
    
    nome_fantasia = nomes_amigaveis.get(cnpj, razao_social.split()[0:3])
    if isinstance(nome_fantasia, list):
        nome_fantasia = ' '.join(nome_fantasia)
    
    # Criar ou atualizar posto
    posto, created = PostoVibra.objects.get_or_create(
        cnpj=cnpj,
        defaults={
            'codigo_vibra': codigo_vibra,
            'razao_social': razao_social,
            'nome_fantasia': nome_fantasia,
        }
    )
    
    if not created:
        # Atualizar informações se já existe
        posto.codigo_vibra = codigo_vibra
        posto.razao_social = razao_social
        posto.nome_fantasia = nome_fantasia
        posto.save()
        print(f"  ✓ Posto atualizado: {posto.nome_fantasia} ({cnpj})")
    else:
        print(f"  ✓ Posto criado: {posto.nome_fantasia} ({cnpj})")
    
    # NÃO deletar preços antigos - manter histórico completo
    # Apenas deletar preços do MESMO DIA (se já existirem) para evitar duplicação
    hoje = timezone.now().date()
    inicio_dia = timezone.make_aware(datetime.combine(hoje, datetime.min.time()))
    fim_dia = timezone.make_aware(datetime.combine(hoje, datetime.max.time()))
    
    precos_deletados = PrecoVibra.objects.filter(
        posto=posto,
        data_coleta__gte=inicio_dia,
        data_coleta__lte=fim_dia
    ).delete()[0]
    
    if precos_deletados > 0:
        print(f"  🗑️  Removidos {precos_deletados} preços de hoje (evitando duplicação)")
    
    # Salvar novos preços
    precos_salvos = 0
    for produto in dados.get('produtos', []):
        # Converter preço de string para decimal
        # Formato: "Preço: R$ 3,6377" ou "R$ 3,6377" -> 3.6377
        preco_str = produto.get('preco', '')
        preco_str = preco_str.replace('Preço:', '').replace('R$', '').replace('.', '').replace(',', '.').strip()
        
        if not preco_str:
            # Produto sem preço (indisponível ou erro)
            continue
            
        try:
            preco_decimal = float(preco_str)
        except:
            print(f"    [WARN] Não foi possível converter preço: {produto.get('preco', '')}")
            continue
        
        PrecoVibra.objects.create(
            posto=posto,
            produto_nome=produto.get('nome', ''),
            produto_codigo=produto.get('codigo', ''),
            preco=preco_decimal,
            prazo_pagamento=produto.get('prazo', ''),
            base_distribuicao=produto.get('base', ''),
            modalidade=dados.get('modalidade', '') or 'Não especificada',
            data_coleta=timezone.now(),
            disponivel=True
        )
        precos_salvos += 1
    
    print(f"  💾 Salvos {precos_salvos} preços")
    
    return (posto.nome_fantasia, precos_salvos)


def importar_arquivo_consolidado():
    """
    Importa o arquivo vibra_precos_TODOS_POSTOS.json com dados de todos os postos
    """
    print("\n" + "="*70)
    print("IMPORTAÇÃO DE PREÇOS VIBRA PARA O BANCO DE DADOS")
    print("="*70 + "\n")
    
    # Buscar arquivo consolidado
    diretorio_atual = Path(__file__).parent
    arquivo_consolidado = diretorio_atual / 'vibra_precos_TODOS_POSTOS.json'
    
    if not arquivo_consolidado.exists():
        print(f"[ERROR] Arquivo não encontrado: {arquivo_consolidado}")
        print("[INFO] Execute primeiro: python vibra_scraper.py")
        return
    
    print(f"[INFO] Importando de: {arquivo_consolidado.name}\n")
    
    # Carregar JSON (é uma lista de postos)
    with open(arquivo_consolidado, 'r', encoding='utf-8') as f:
        lista_postos = json.load(f)
    
    print(f"[INFO] Encontrados {len(lista_postos)} postos no arquivo\n")
    
    total_postos = 0
    total_precos = 0
    erros = []
    
    for dados in lista_postos:
        codigo = dados.get('codigo_vibra', 'SEM_CODIGO')
        nome = dados.get('razao_social', 'SEM_NOME')
        print(f"📁 Importando: {codigo} - {nome}")
        try:
            nome_posto, precos_salvos = importar_json_individual(dados)
            if nome_posto:
                total_postos += 1
                total_precos += precos_salvos
        except Exception as e:
            print(f"  [ERROR] Erro ao importar: {e}")
            erros.append((f"{codigo} - {nome}", str(e)))
        print()
    
    # Resumo final
    print("="*70)
    print("IMPORTAÇÃO CONCLUÍDA")
    print("="*70)
    print(f"✅ Postos importados: {total_postos}/{len(lista_postos)}")
    print(f"✅ Preços salvos: {total_precos}")
    
    if erros:
        print(f"\n⚠️  Erros encontrados: {len(erros)}")
        for posto, erro in erros:
            print(f"  - {posto}: {erro}")
    
    print("\n[INFO] Verificação no banco:")
    print(f"  Total de postos: {PostoVibra.objects.count()}")
    print(f"  Total de preços: {PrecoVibra.objects.count()}")
    print("="*70 + "\n")


if __name__ == '__main__':
    importar_arquivo_consolidado()
