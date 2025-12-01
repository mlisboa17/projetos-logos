"""
Script para importar produtos da planilha para o banco de dados
- Verifica duplicidade pelo código de barras
- Cria categorias e recipientes automaticamente
- Extrai marca da descrição
- Salva produtos não importados em arquivo separado
"""
import os
import sys
import django
import pandas as pd
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from verifik.models import ProdutoMae, CodigoBarrasProdutoMae, Categoria, Marca, Recipiente


def extrair_marca_da_descricao(descricao):
    """Tenta extrair a marca da descrição do produto"""
    descricao = descricao.upper()
    
    # Lista de marcas conhecidas
    marcas_conhecidas = {
        # Águas
        'CRYSTAL': 'Crystal',
        'MINALBA': 'Minalba',
        'INDAIA': 'Indaiá',
        'PETROPOLIS': 'Petrópolis',
        'DUDELI': 'Dudeli',
        # Energéticos
        'RED BULL': 'Red Bull',
        'REDBULL': 'Red Bull',
        'MONSTER': 'Monster',
        'TNT': 'TNT',
        'FUSION': 'Fusion',
        # Refrigerantes
        'COCA COLA': 'Coca-Cola',
        'COCA-COLA': 'Coca-Cola',
        'COCA': 'Coca-Cola',
        'PEPSI': 'Pepsi',
        'GUARANA': 'Guaraná Antarctica',
        'GUARANÁ': 'Guaraná Antarctica',
        'ANTARCTICA': 'Antarctica',
        'FANTA': 'Fanta',
        'SPRITE': 'Sprite',
        'SCHWEPPES': 'Schweppes',
        'KUAT': 'Kuat',
        'H2OH': 'H2OH',
        'SUKITA': 'Sukita',
        # Sucos
        'DEL VALLE': 'Del Valle',
        'DELVALLE': 'Del Valle',
        'SUFRESH': 'Sufresh',
        'MARATA': 'Maratá',
        'MAGUARY': 'Maguary',
        # Chás
        'LEAO': 'Leão',
        'MATTE LEAO': 'Matte Leão',
        'FEEL GOOD': 'Feel Good',
        # Cervejas (caso tenha)
        'HEINEKEN': 'Heineken',
        'AMSTEL': 'Amstel',
        'STELLA': 'Stella Artois',
        'BUDWEISER': 'Budweiser',
        'CORONA': 'Corona',
        'BRAHMA': 'Brahma',
        'SKOL': 'Skol',
        'DEVASSA': 'Devassa',
        'EISENBAHN': 'Eisenbahn',
        'LOKAL': 'Lokal',
    }
    
    for chave, marca in marcas_conhecidas.items():
        if chave in descricao:
            return marca
    
    return None


def normalizar_recipiente(recipiente):
    """Normaliza o nome do recipiente"""
    if pd.isna(recipiente) or not recipiente:
        return None
    
    recipiente = str(recipiente).upper().strip()
    
    # Mapeamento de normalização
    mapa = {
        'LATA 350ML': 'LATA 350ML',
        'LATA': 'LATA 350ML',
        'LATAO': 'LATÃO 473ML',
        'LATÃO': 'LATÃO 473ML',
        'PET': 'PET',
        'PET 500 ML': 'PET 500ML',
        'PET 500ML': 'PET 500ML',
        'PET 250ML': 'PET 250ML',
        'PET 1 LITRO': 'PET 1L',
        'PET 1LT': 'PET 1L',
        'PET 1L': 'PET 1L',
        'PET 2L': 'PET 2L',
        'PET 2LT': 'PET 2L',
        'PET OUTROS': 'PET',
        'GARRAFA': 'GARRAFA',
        'GARRAFA ': 'GARRAFA',
        'CAIXA': 'CAIXA',
        'CAIXA 1LT': 'CAIXA 1L',
        'COPO': 'COPO',
        'PACOTE': 'PACOTE',
        'PACOTE 18G': 'PACOTE',
        'REDBULL': 'LATA 250ML',  # Red Bull é lata 250ml
        'MONSTER': 'LATA 473ML',   # Monster é latão
    }
    
    return mapa.get(recipiente, recipiente)


def obter_volume_ml(recipiente_nome):
    """Retorna o volume em ML baseado no nome do recipiente"""
    volumes = {
        'LATA 350ML': 350,
        'LATA 250ML': 250,
        'LATÃO 473ML': 473,
        'PET 250ML': 250,
        'PET 500ML': 500,
        'PET 600ML': 600,
        'PET 1L': 1000,
        'PET 2L': 2000,
        'GARRAFA': 600,
        'CAIXA 1L': 1000,
    }
    return volumes.get(recipiente_nome)


def importar_planilha(caminho_planilha):
    """Importa produtos da planilha para o banco de dados"""
    
    print("=" * 60)
    print("🚀 IMPORTAÇÃO DE PRODUTOS")
    print("=" * 60)
    
    # Ler planilha
    df = pd.read_excel(caminho_planilha)
    print(f"📄 Planilha carregada: {len(df)} produtos")
    
    # Contadores
    importados = 0
    duplicados = []
    erros = []
    
    # Cache de objetos criados
    categorias_cache = {}
    marcas_cache = {}
    recipientes_cache = {}
    
    print("\n📦 Processando produtos...\n")
    
    for idx, row in df.iterrows():
        codigo_barras = str(row['Código']).strip()
        descricao = str(row['Descrição']).strip()
        categoria_nome = str(row['CATEGORIA']).strip() if pd.notna(row['CATEGORIA']) else None
        recipiente_nome = normalizar_recipiente(row['RECIPIENTE'])
        preco = float(row['Preço Venda']) if pd.notna(row['Preço Venda']) else 0.0
        
        try:
            # 1. Verificar se código de barras já existe
            codigo_existente = CodigoBarrasProdutoMae.objects.filter(codigo=codigo_barras).first()
            
            if codigo_existente:
                # Já existe - adicionar à lista de duplicados
                duplicados.append({
                    'codigo': codigo_barras,
                    'descricao_planilha': descricao,
                    'descricao_banco': codigo_existente.produto_mae.descricao_produto,
                    'motivo': 'Código de barras já existe'
                })
                print(f"⚠️  DUPLICADO: {codigo_barras} - {descricao[:40]}...")
                continue
            
            # 2. Criar/obter Categoria
            categoria_obj = None
            if categoria_nome:
                if categoria_nome not in categorias_cache:
                    categoria_obj, created = Categoria.objects.get_or_create(
                        nome=categoria_nome,
                        defaults={'descricao': f'Categoria: {categoria_nome}'}
                    )
                    categorias_cache[categoria_nome] = categoria_obj
                    if created:
                        print(f"   📁 Nova categoria criada: {categoria_nome}")
                else:
                    categoria_obj = categorias_cache[categoria_nome]
            
            # 3. Extrair e criar/obter Marca
            marca_nome = extrair_marca_da_descricao(descricao)
            marca_obj = None
            if marca_nome:
                if marca_nome not in marcas_cache:
                    marca_obj, created = Marca.objects.get_or_create(
                        nome=marca_nome,
                        defaults={'categoria': categoria_obj}
                    )
                    marcas_cache[marca_nome] = marca_obj
                    if created:
                        print(f"   🏷️  Nova marca criada: {marca_nome}")
                else:
                    marca_obj = marcas_cache[marca_nome]
            
            # 4. Criar/obter Recipiente
            recipiente_obj = None
            if recipiente_nome:
                if recipiente_nome not in recipientes_cache:
                    volume = obter_volume_ml(recipiente_nome)
                    recipiente_obj, created = Recipiente.objects.get_or_create(
                        nome=recipiente_nome,
                        defaults={'volume_ml': volume}
                    )
                    recipientes_cache[recipiente_nome] = recipiente_obj
                    if created:
                        print(f"   📦 Novo recipiente criado: {recipiente_nome}")
                else:
                    recipiente_obj = recipientes_cache[recipiente_nome]
            
            # 5. Criar ProdutoMae
            produto = ProdutoMae.objects.create(
                descricao_produto=descricao,
                categoria_fk=categoria_obj,
                marca_fk=marca_obj,
                recipiente_fk=recipiente_obj,
                marca=marca_nome or '',  # Campo legado
                tipo=categoria_nome or '',  # Campo legado
                preco=preco,
                ativo=True,
                treinado=False,
                qtd_imagens_treino=0,
                total_deteccoes=0,
                total_acertos=0,
                total_erros=0
            )
            
            # 6. Criar código de barras
            CodigoBarrasProdutoMae.objects.create(
                produto_mae=produto,
                codigo=codigo_barras,
                principal=True
            )
            
            importados += 1
            print(f"✅ IMPORTADO: {codigo_barras} - {descricao[:40]}...")
            
        except Exception as e:
            erros.append({
                'codigo': codigo_barras,
                'descricao': descricao,
                'erro': str(e)
            })
            print(f"❌ ERRO: {codigo_barras} - {str(e)}")
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL")
    print("=" * 60)
    print(f"✅ Importados: {importados}")
    print(f"⚠️  Duplicados: {len(duplicados)}")
    print(f"❌ Erros: {len(erros)}")
    print(f"📁 Categorias criadas: {len([c for c in categorias_cache.values()])}")
    print(f"🏷️  Marcas criadas: {len([m for m in marcas_cache.values()])}")
    print(f"📦 Recipientes criados: {len([r for r in recipientes_cache.values()])}")
    
    # Salvar não importados em arquivo
    if duplicados or erros:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        arquivo_saida = f'produtos_nao_importados_{timestamp}.xlsx'
        
        # Criar DataFrame com duplicados e erros
        dados_saida = []
        for d in duplicados:
            dados_saida.append({
                'Código': d['codigo'],
                'Descrição Planilha': d['descricao_planilha'],
                'Descrição Banco': d.get('descricao_banco', ''),
                'Motivo': d['motivo'],
                'Tipo': 'DUPLICADO'
            })
        for e in erros:
            dados_saida.append({
                'Código': e['codigo'],
                'Descrição Planilha': e['descricao'],
                'Descrição Banco': '',
                'Motivo': e['erro'],
                'Tipo': 'ERRO'
            })
        
        df_saida = pd.DataFrame(dados_saida)
        df_saida.to_excel(arquivo_saida, index=False)
        print(f"\n📄 Arquivo de não importados salvo: {arquivo_saida}")
    
    return importados, duplicados, erros


if __name__ == '__main__':
    caminho = r'C:\Users\gabri\Downloads\PosicaoEstoque_49 (1) (2).xlsx'
    importar_planilha(caminho)
