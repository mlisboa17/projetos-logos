"""
Script para classificar todos os produtos do banco de dados
com Categoria, Marca e Recipiente apropriados.
"""
import os
import sys
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from verifik.models import ProdutoMae, Categoria, Marca, Recipiente

# =============================================================================
# DEFINIÇÕES DE CATEGORIAS, MARCAS E RECIPIENTES
# =============================================================================

# Categorias a serem criadas
CATEGORIAS = {
    'CERVEJA': 'Cervejas em geral (pilsen, lager, IPA, etc.)',
    'REFRIGERANTE': 'Refrigerantes em geral',
    'AGUA TONICA': 'Água tônica e bebidas similares',
    'BEBIDA ALCOOLICA MISTA': 'Bebidas alcoólicas mistas (ice, drinks)',
    'SUCO / BEBIDAS NATURAIS': 'Sucos e bebidas naturais',
    'AGUA': 'Águas minerais e com gás',
    'ENERGETICO': 'Bebidas energéticas',
    'CHA': 'Chás prontos',
    'SALGADINHO': 'Salgadinhos e snacks',
}

# Marcas a serem criadas com suas categorias e aliases
MARCAS = {
    # CERVEJAS
    'HEINEKEN': {'categoria': 'CERVEJA', 'aliases': ['HEINEKEN', 'HEINEIKEN', 'HEIN']},
    'AMSTEL': {'categoria': 'CERVEJA', 'aliases': ['AMSTEL', 'AMST']},
    'BUDWEISER': {'categoria': 'CERVEJA', 'aliases': ['BUDWEISER', 'BUD']},
    'BRAHMA': {'categoria': 'CERVEJA', 'aliases': ['BRAHMA', 'BRAMA']},
    'SKOL': {'categoria': 'CERVEJA', 'aliases': ['SKOL']},
    'CORONA': {'categoria': 'CERVEJA', 'aliases': ['CORONA', 'CORONITA']},
    'STELLA ARTOIS': {'categoria': 'CERVEJA', 'aliases': ['STELLA ARTOIS', 'STELLA', 'STELLAARTOIS']},
    'BOHEMIA': {'categoria': 'CERVEJA', 'aliases': ['BOHEMIA', 'BOHEMIAN']},
    'ORIGINAL': {'categoria': 'CERVEJA', 'aliases': ['ORIGINAL']},
    'ANTARCTICA': {'categoria': 'CERVEJA', 'aliases': ['ANTARCTICA', 'ANTARTICA']},
    'ITAIPAVA': {'categoria': 'CERVEJA', 'aliases': ['ITAIPAVA']},
    'DEVASSA': {'categoria': 'CERVEJA', 'aliases': ['DEVASSA']},
    'IMPERIO': {'categoria': 'CERVEJA', 'aliases': ['IMPERIO', 'IMPÉRIO']},
    'SPATEN': {'categoria': 'CERVEJA', 'aliases': ['SPATEN']},
    'EISENBAHN': {'categoria': 'CERVEJA', 'aliases': ['EISENBAHN']},
    'COLORADO': {'categoria': 'CERVEJA', 'aliases': ['COLORADO', 'APPIA']},
    'BADEN BADEN': {'categoria': 'CERVEJA', 'aliases': ['BADEN BADEN', 'BADEN']},
    'PATAGONIA': {'categoria': 'CERVEJA', 'aliases': ['PATAGONIA']},
    'PETRA': {'categoria': 'CERVEJA', 'aliases': ['PETRA']},
    'BLUE MOON': {'categoria': 'CERVEJA', 'aliases': ['BLUE MOON', 'BLUEMOON']},
    'BLACK PRINCESS': {'categoria': 'CERVEJA', 'aliases': ['BLACK PRINCESS']},
    'CAPUNGA': {'categoria': 'CERVEJA', 'aliases': ['CAPUNGA']},
    'DUVALIA': {'categoria': 'CERVEJA', 'aliases': ['DUVALIA']},
    'ESTRELLA GALICIA': {'categoria': 'CERVEJA', 'aliases': ['ESTRELLA GALICIA', 'STRELLA GALICIA', 'GALICIA']},
    'MICHELOB': {'categoria': 'CERVEJA', 'aliases': ['MICHELOB']},
    'OKTOBER': {'categoria': 'CERVEJA', 'aliases': ['OKTOBER']},
    'LOKAL': {'categoria': 'CERVEJA', 'aliases': ['LOKAL']},
    'SCHIN': {'categoria': 'CERVEJA', 'aliases': ['SCHIN']},
    'SOL': {'categoria': 'CERVEJA', 'aliases': ['SOL PREMIUM', 'SOL']},
    'VOLD': {'categoria': 'CERVEJA', 'aliases': ['VOLD']},
    'CACILDIS': {'categoria': 'CERVEJA', 'aliases': ['CACILDIS']},
    'CABARE': {'categoria': 'CERVEJA', 'aliases': ['CABARE', 'CABARÉ']},
    
    # REFRIGERANTES
    'COCA COLA': {'categoria': 'REFRIGERANTE', 'aliases': ['COCA COLA', 'COCA-COLA', 'COLA']},
    'PEPSI': {'categoria': 'REFRIGERANTE', 'aliases': ['PEPSI', 'PEPSIBLACK']},
    'FANTA': {'categoria': 'REFRIGERANTE', 'aliases': ['FANTA']},
    'SPRITE': {'categoria': 'REFRIGERANTE', 'aliases': ['SPRITE']},
    'GUARANA ANTARCTICA': {'categoria': 'REFRIGERANTE', 'aliases': ['GUARANA ANTARCTICA', 'GUARANA ANT', 'GUARANÁ ANTARCTICA']},
    'KUAT': {'categoria': 'REFRIGERANTE', 'aliases': ['KUAT']},
    'SUKITA': {'categoria': 'REFRIGERANTE', 'aliases': ['SUKITA']},
    'H2OH': {'categoria': 'REFRIGERANTE', 'aliases': ['H2OH', 'H2O']},
    'FYS': {'categoria': 'REFRIGERANTE', 'aliases': ['FYS']},
    'SODA ANTARCTICA': {'categoria': 'REFRIGERANTE', 'aliases': ['SODA', 'SODA LIMONADA', 'SODA LIMONADA ANTARCTICA']},
    'IT': {'categoria': 'REFRIGERANTE', 'aliases': ['COLA IT', 'GUARANA IT', 'LARANJA IT', 'LIMAO IT']},
    'GUARANA JESUS': {'categoria': 'REFRIGERANTE', 'aliases': ['GUARANA JESUS', 'JESUS']},
    
    # AGUA TONICA
    'SCHWEPPES': {'categoria': 'AGUA TONICA', 'aliases': ['SCHWEPPES']},
    'ANTARCTICA TONICA': {'categoria': 'AGUA TONICA', 'aliases': ['AGUA TONICA ANTARCTICA', 'TONICA ANTARCTICA']},
    
    # BEBIDAS ALCOOLICAS MISTAS
    'SMIRNOFF': {'categoria': 'BEBIDA ALCOOLICA MISTA', 'aliases': ['SMIRNOFF', 'SMIRNOFF ICE']},
    'SKOL BEATS': {'categoria': 'BEBIDA ALCOOLICA MISTA', 'aliases': ['SKOL BEATS', 'BEATS']},
    
    # SUCO
    'DEL VALLE': {'categoria': 'SUCO / BEBIDAS NATURAIS', 'aliases': ['DEL VALLE', 'DELVALLE']},
    
    # SALGADINHOS
    'RUFFLES': {'categoria': 'SALGADINHO', 'aliases': ['RUFFLES']},
    'PRINGLES': {'categoria': 'SALGADINHO', 'aliases': ['PRINGLES']},
    'PIPOCA BOKUS': {'categoria': 'SALGADINHO', 'aliases': ['PIPOCABOKUS', 'BOKUS']},
}

# Recipientes com volumes e aliases
RECIPIENTES = {
    'LATA 269ML': {'volume_ml': 269, 'aliases': ['LATA 269ML', 'LT 269', '269ML LATA']},
    'LATA 220ML': {'volume_ml': 220, 'aliases': ['LATA 220ML', 'LT 220', '220ML']},
    'LATA 350ML': {'volume_ml': 350, 'aliases': ['LATA 350ML', 'LT 350ML', '350ML LATA', 'LATA 350', 'LT 350']},
    'LATÃO 473ML': {'volume_ml': 473, 'aliases': ['LATAO 473ML', 'LATÃO 473ML', 'LT 473ML', '473ML LATA', '473ML LATAO', '473ML', 'LATAO']},
    'LATÃO 550ML': {'volume_ml': 550, 'aliases': ['LATAO 550ML', 'LATÃO 550ML', '550ML']},
    'LONG NECK 275ML': {'volume_ml': 275, 'aliases': ['275ML LONG', 'LONG NECK 275ML', 'LONGNECK 275ML', '275ML']},
    'LONG NECK 330ML': {'volume_ml': 330, 'aliases': ['LONG NECK 330ML', 'LN 330ML', 'LONGNECK 330ML', '330ML', 'LONG NECK', 'LN']},
    'LONG NECK 355ML': {'volume_ml': 355, 'aliases': ['LONG NECK 355ML', 'LN 355ML', 'LONGNECK 355ML', '355ML']},
    'GARRAFA 200ML': {'volume_ml': 200, 'aliases': ['GARRAFA 200ML', '200ML']},
    'GARRAFA 210ML': {'volume_ml': 210, 'aliases': ['GARRAFA 210ML', '210ML']},
    'GARRAFA 500ML': {'volume_ml': 500, 'aliases': ['GARRAFA 500ML', '500ML']},
    'GARRAFA 600ML': {'volume_ml': 600, 'aliases': ['GARRAFA 600ML', 'GF 600ML', '600ML']},
    'PET 250ML': {'volume_ml': 250, 'aliases': ['PET 250ML', '250ML']},
    'PET 500ML': {'volume_ml': 500, 'aliases': ['PET 500ML']},
    'PET 510ML': {'volume_ml': 510, 'aliases': ['PET 510ML', '510ML']},
    'PET 1L': {'volume_ml': 1000, 'aliases': ['PET 1L', '1L', '1 L', '1 LITRO', '1000ML', 'GARRAFA 1L', 'GARRAFA PET 1']},
    'PET 1,5L': {'volume_ml': 1500, 'aliases': ['PET 1,5L', '1,5L', '1,5 L', '1500ML']},
    'PET 2L': {'volume_ml': 2000, 'aliases': ['PET 2L', '2L', '2 L', '2 LITROS', '2000ML', 'GARRAFA 2L']},
    'BARRIL 5L': {'volume_ml': 5000, 'aliases': ['BARRIL', '5 LITROS', '5L']},
}

def normalizar_texto(texto):
    """Remove acentos e converte para maiúsculas"""
    import unicodedata
    texto = texto.upper()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(char for char in texto if unicodedata.category(char) != 'Mn')
    return texto

def criar_categorias():
    """Cria todas as categorias necessárias"""
    print("\n" + "="*60)
    print("CRIANDO CATEGORIAS")
    print("="*60)
    
    for nome, descricao in CATEGORIAS.items():
        cat, created = Categoria.objects.get_or_create(
            nome=nome,
            defaults={'descricao': descricao, 'ativo': True}
        )
        if created:
            print(f"  ✅ Criada: {nome}")
        else:
            print(f"  ⏭️  Já existe: {nome}")
    
    print(f"\nTotal de categorias: {Categoria.objects.count()}")

def criar_marcas():
    """Cria todas as marcas necessárias"""
    print("\n" + "="*60)
    print("CRIANDO MARCAS")
    print("="*60)
    
    for nome, info in MARCAS.items():
        # Busca a categoria
        try:
            categoria = Categoria.objects.get(nome=info['categoria'])
        except Categoria.DoesNotExist:
            print(f"  ❌ Categoria não encontrada: {info['categoria']}")
            continue
        
        aliases_str = ','.join(info['aliases'])
        
        marca, created = Marca.objects.get_or_create(
            nome=nome,
            defaults={
                'aliases': aliases_str,
                'categoria': categoria,
                'ativo': True
            }
        )
        if created:
            print(f"  ✅ Criada: {nome} ({info['categoria']})")
        else:
            print(f"  ⏭️  Já existe: {nome}")
    
    print(f"\nTotal de marcas: {Marca.objects.count()}")

def criar_recipientes():
    """Cria todos os recipientes necessários"""
    print("\n" + "="*60)
    print("CRIANDO RECIPIENTES")
    print("="*60)
    
    for nome, info in RECIPIENTES.items():
        aliases_str = ','.join(info['aliases'])
        
        rec, created = Recipiente.objects.get_or_create(
            nome=nome,
            defaults={
                'volume_ml': info['volume_ml'],
                'aliases': aliases_str,
                'ativo': True
            }
        )
        if created:
            print(f"  ✅ Criado: {nome} ({info['volume_ml']}ml)")
        else:
            print(f"  ⏭️  Já existe: {nome}")
    
    print(f"\nTotal de recipientes: {Recipiente.objects.count()}")

def detectar_categoria(descricao):
    """Detecta a categoria pelo nome do produto"""
    desc_norm = normalizar_texto(descricao)
    
    # Ordem de prioridade na detecção
    if 'CERVEJA' in desc_norm or any(marca in desc_norm for marca in 
        ['HEINEKEN', 'AMSTEL', 'BUDWEISER', 'BRAHMA', 'SKOL', 'CORONA', 
         'STELLA', 'BOHEMIA', 'ITAIPAVA', 'DEVASSA', 'IMPERIO', 'SPATEN',
         'EISENBAHN', 'COLORADO', 'APPIA', 'BADEN', 'PATAGONIA', 'PETRA',
         'BLUE MOON', 'BLACK PRINCESS', 'CAPUNGA', 'DUVALIA', 'ESTRELLA',
         'MICHELOB', 'OKTOBER', 'LOKAL', 'SCHIN', 'SOL', 'VOLD', 'CACILDIS',
         'CABARE', 'ORIGINAL', 'CHOPP']):
        return 'CERVEJA'
    
    if 'SMIRNOFF' in desc_norm or 'SKOL BEATS' in desc_norm:
        return 'BEBIDA ALCOOLICA MISTA'
    
    if 'AGUA TONICA' in desc_norm or ('SCHWEPPES' in desc_norm and 'CITRUS' not in desc_norm and 'GINGER' in desc_norm):
        return 'AGUA TONICA'
    
    if any(x in desc_norm for x in ['REFRIGERANTE', 'REFRI', 'REFRIG', 'REFR']):
        return 'REFRIGERANTE'
    
    if any(x in desc_norm for x in ['COCA COLA', 'PEPSI', 'FANTA', 'SPRITE', 
        'GUARANA', 'KUAT', 'SUKITA', 'H2OH', 'H2O', 'FYS', 'SODA']):
        return 'REFRIGERANTE'
    
    if 'SCHWEPPES' in desc_norm:
        if 'CITRUS' in desc_norm:
            return 'REFRIGERANTE'
        return 'AGUA TONICA'
    
    if 'SUCO' in desc_norm or 'DEL VALLE' in desc_norm:
        return 'SUCO / BEBIDAS NATURAIS'
    
    if any(x in desc_norm for x in ['RUFFLES', 'PRINGLES', 'PIPOCA', 'SALGAD']):
        return 'SALGADINHO'
    
    if 'ENERGETICO' in desc_norm or any(x in desc_norm for x in ['MONSTER', 'RED BULL', 'TNT', 'FUSION']):
        return 'ENERGETICO'
    
    if 'CHA' in desc_norm or 'LEAO' in desc_norm:
        return 'CHA'
    
    if 'AGUA' in desc_norm and 'TONICA' not in desc_norm:
        return 'AGUA'
    
    return None

def detectar_marca(descricao, categoria):
    """Detecta a marca pelo nome do produto"""
    desc_norm = normalizar_texto(descricao)
    
    # Filtrar marcas pela categoria
    marcas_categoria = {nome: info for nome, info in MARCAS.items() 
                        if info['categoria'] == categoria}
    
    # Tentar encontrar a marca
    for nome_marca, info in marcas_categoria.items():
        for alias in info['aliases']:
            alias_norm = normalizar_texto(alias)
            if alias_norm in desc_norm:
                return nome_marca
    
    # Se não encontrou na categoria, buscar em todas as marcas
    for nome_marca, info in MARCAS.items():
        for alias in info['aliases']:
            alias_norm = normalizar_texto(alias)
            if alias_norm in desc_norm:
                return nome_marca
    
    return None

def detectar_recipiente(descricao):
    """Detecta o recipiente pelo nome do produto"""
    desc_norm = normalizar_texto(descricao)
    
    # Padrões de volume com regex
    volume_patterns = [
        (r'(\d+)\s*ML', None),
        (r'(\d+(?:,\d+)?)\s*L(?:ITROS?)?', 'L'),
    ]
    
    # Primeiro, tentar detectar pelo tipo de recipiente explícito
    if 'BARRIL' in desc_norm or 'CHOPP' in desc_norm:
        return 'BARRIL 5L'
    
    # Detectar tipo de recipiente
    tipo_recipiente = None
    if 'LONG NECK' in desc_norm or 'LONGNECK' in desc_norm or ' LN ' in desc_norm or desc_norm.endswith(' LN'):
        tipo_recipiente = 'LONG NECK'
    elif 'LATAO' in desc_norm or 'LATÃO' in desc_norm:
        tipo_recipiente = 'LATÃO'
    elif 'LATA' in desc_norm or ' LT ' in desc_norm or desc_norm.startswith('LT '):
        tipo_recipiente = 'LATA'
    elif 'PET' in desc_norm:
        tipo_recipiente = 'PET'
    elif 'GARRAFA' in desc_norm or ' GF ' in desc_norm:
        tipo_recipiente = 'GARRAFA'
    
    # Extrair volume
    volume_ml = None
    
    # Buscar padrão de ML
    match_ml = re.search(r'(\d+)\s*ML', desc_norm)
    if match_ml:
        volume_ml = int(match_ml.group(1))
    
    # Buscar padrão de L
    if not volume_ml:
        match_l = re.search(r'(\d+(?:,\d+)?)\s*L(?:ITROS?)?(?!\w)', desc_norm)
        if match_l:
            vol_str = match_l.group(1).replace(',', '.')
            volume_ml = int(float(vol_str) * 1000)
    
    # Mapear volume + tipo para recipiente
    if volume_ml:
        # Mapeamento por volume
        volume_mapping = {
            200: 'GARRAFA 200ML',
            210: 'GARRAFA 210ML',
            220: 'LATA 220ML',
            250: 'PET 250ML',
            269: 'LATA 269ML',
            275: 'LONG NECK 275ML',
            330: 'LONG NECK 330ML',
            350: 'LATA 350ML',
            355: 'LONG NECK 355ML',
            473: 'LATÃO 473ML',
            500: 'GARRAFA 500ML',
            510: 'PET 510ML',
            550: 'LATÃO 550ML',
            600: 'GARRAFA 600ML',
            1000: 'PET 1L',
            1500: 'PET 1,5L',
            2000: 'PET 2L',
            5000: 'BARRIL 5L',
        }
        
        # Ajustar baseado no tipo de recipiente
        if tipo_recipiente == 'LONG NECK':
            if volume_ml == 275:
                return 'LONG NECK 275ML'
            elif volume_ml == 330:
                return 'LONG NECK 330ML'
            elif volume_ml == 355:
                return 'LONG NECK 355ML'
        elif tipo_recipiente == 'LATÃO':
            if volume_ml == 473:
                return 'LATÃO 473ML'
            elif volume_ml == 550:
                return 'LATÃO 550ML'
        elif tipo_recipiente == 'LATA':
            if volume_ml == 220:
                return 'LATA 220ML'
            elif volume_ml == 269:
                return 'LATA 269ML'
            elif volume_ml == 350:
                return 'LATA 350ML'
        elif tipo_recipiente == 'PET':
            if volume_ml == 250:
                return 'PET 250ML'
            elif volume_ml == 500:
                return 'PET 500ML'
            elif volume_ml == 510:
                return 'PET 510ML'
            elif volume_ml == 1000:
                return 'PET 1L'
            elif volume_ml == 1500:
                return 'PET 1,5L'
            elif volume_ml == 2000:
                return 'PET 2L'
        elif tipo_recipiente == 'GARRAFA':
            if volume_ml == 200:
                return 'GARRAFA 200ML'
            elif volume_ml == 210:
                return 'GARRAFA 210ML'
            elif volume_ml == 500:
                return 'GARRAFA 500ML'
            elif volume_ml == 600:
                return 'GARRAFA 600ML'
            elif volume_ml == 1000:
                return 'PET 1L'
            elif volume_ml == 2000:
                return 'PET 2L'
        
        # Se não encontrou específico, usar mapeamento genérico
        if volume_ml in volume_mapping:
            return volume_mapping[volume_ml]
    
    return None

def classificar_produtos():
    """Classifica todos os produtos sem categoria/marca/recipiente"""
    print("\n" + "="*60)
    print("CLASSIFICANDO PRODUTOS")
    print("="*60)
    
    # Buscar todos os produtos
    produtos = ProdutoMae.objects.all()
    
    total = produtos.count()
    classificados_cat = 0
    classificados_marca = 0
    classificados_rec = 0
    erros = []
    
    for produto in produtos:
        descricao = produto.descricao_produto or ''
        
        if not descricao or descricao == 'DESCONHECIDO':
            continue
        
        alterado = False
        
        # Classificar categoria se não tiver
        if not produto.categoria_fk:
            categoria_nome = detectar_categoria(descricao)
            if categoria_nome:
                try:
                    categoria = Categoria.objects.get(nome=categoria_nome)
                    produto.categoria_fk = categoria
                    classificados_cat += 1
                    alterado = True
                except Categoria.DoesNotExist:
                    erros.append(f"Categoria não encontrada: {categoria_nome} para {descricao}")
        
        # Classificar marca se não tiver
        if not produto.marca_fk:
            categoria_nome = produto.categoria_fk.nome if produto.categoria_fk else detectar_categoria(descricao)
            if categoria_nome:
                marca_nome = detectar_marca(descricao, categoria_nome)
                if marca_nome:
                    try:
                        marca = Marca.objects.get(nome=marca_nome)
                        produto.marca_fk = marca
                        classificados_marca += 1
                        alterado = True
                    except Marca.DoesNotExist:
                        erros.append(f"Marca não encontrada: {marca_nome} para {descricao}")
        
        # Classificar recipiente se não tiver
        if not produto.recipiente_fk:
            recipiente_nome = detectar_recipiente(descricao)
            if recipiente_nome:
                try:
                    recipiente = Recipiente.objects.get(nome=recipiente_nome)
                    produto.recipiente_fk = recipiente
                    classificados_rec += 1
                    alterado = True
                except Recipiente.DoesNotExist:
                    erros.append(f"Recipiente não encontrado: {recipiente_nome} para {descricao}")
        
        if alterado:
            produto.save()
    
    print(f"\n📊 RESULTADO:")
    print(f"  Total de produtos: {total}")
    print(f"  Categorias atribuídas: {classificados_cat}")
    print(f"  Marcas atribuídas: {classificados_marca}")
    print(f"  Recipientes atribuídos: {classificados_rec}")
    
    if erros:
        print(f"\n⚠️  ERROS ({len(erros)}):")
        for erro in erros[:10]:
            print(f"  - {erro}")
        if len(erros) > 10:
            print(f"  ... e mais {len(erros) - 10} erros")

def mostrar_resumo():
    """Mostra resumo final da classificação"""
    print("\n" + "="*60)
    print("RESUMO FINAL")
    print("="*60)
    
    total = ProdutoMae.objects.count()
    com_categoria = ProdutoMae.objects.exclude(categoria_fk__isnull=True).count()
    com_marca = ProdutoMae.objects.exclude(marca_fk__isnull=True).count()
    com_recipiente = ProdutoMae.objects.exclude(recipiente_fk__isnull=True).count()
    
    print(f"\n📦 PRODUTOS:")
    print(f"  Total: {total}")
    print(f"  Com categoria: {com_categoria} ({100*com_categoria/total:.1f}%)")
    print(f"  Com marca: {com_marca} ({100*com_marca/total:.1f}%)")
    print(f"  Com recipiente: {com_recipiente} ({100*com_recipiente/total:.1f}%)")
    
    print(f"\n📁 CATEGORIAS ({Categoria.objects.count()}):")
    for cat in Categoria.objects.all():
        qtd = ProdutoMae.objects.filter(categoria_fk=cat).count()
        print(f"  - {cat.nome}: {qtd} produtos")
    
    print(f"\n🏷️  MARCAS TOP 15:")
    marcas = Marca.objects.all()
    marcas_qtd = [(m, ProdutoMae.objects.filter(marca_fk=m).count()) for m in marcas]
    marcas_qtd.sort(key=lambda x: x[1], reverse=True)
    for marca, qtd in marcas_qtd[:15]:
        if qtd > 0:
            print(f"  - {marca.nome}: {qtd} produtos")
    
    print(f"\n📦 RECIPIENTES:")
    for rec in Recipiente.objects.all():
        qtd = ProdutoMae.objects.filter(recipiente_fk=rec).count()
        if qtd > 0:
            print(f"  - {rec.nome}: {qtd} produtos")
    
    # Mostrar produtos sem classificação
    sem_cat = ProdutoMae.objects.filter(categoria_fk__isnull=True)
    if sem_cat.exists():
        print(f"\n⚠️  PRODUTOS SEM CATEGORIA ({sem_cat.count()}):")
        for p in sem_cat[:10]:
            print(f"  - {p.descricao_produto}")
        if sem_cat.count() > 10:
            print(f"  ... e mais {sem_cat.count() - 10}")

if __name__ == '__main__':
    print("="*60)
    print("  CLASSIFICAÇÃO AUTOMÁTICA DE PRODUTOS")
    print("="*60)
    
    # 1. Criar categorias
    criar_categorias()
    
    # 2. Criar marcas
    criar_marcas()
    
    # 3. Criar recipientes
    criar_recipientes()
    
    # 4. Classificar produtos
    classificar_produtos()
    
    # 5. Mostrar resumo
    mostrar_resumo()
    
    print("\n✅ PROCESSO CONCLUÍDO!")
