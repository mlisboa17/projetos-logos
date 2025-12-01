#!/usr/bin/env python
"""
Script Genérico de Processamento de Imagens
Permite processar imagens com múltiplos filtros e tipos de processamento
"""
import django
import os
import sys
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

# Fix encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from verifik.models import ProdutoMae, ImagemProduto, Categoria, Marca
from verifik.models_anotacao import ImagemAnotada
from acessorios.processador import ProcessadorImagensGenerico
from acessorios.filtrador import FiltrorImagens
from acessorios.models import ProcessadorImagens as ProcessadorImagensLog
from datetime import datetime


class ProcessadorEmLote:
    """Gerenciador de processamento em lote"""
    
    def __init__(self):
        self.processador = ProcessadorImagensGenerico()
        self.filtrador = FiltrorImagens(ImagemProduto)
        
    def listar_categorias(self):
        """Lista todas as categorias disponíveis"""
        categorias = Categoria.objects.all()
        print("\n" + "=" * 80)
        print("📂 CATEGORIAS DISPONÍVEIS")
        print("=" * 80)
        for cat in categorias:
            count = ImagemProduto.objects.filter(produto__categoria=cat).count()
            print(f"  ID {cat.id}: {cat.nome} ({count} imagens)")
        print()
        return categorias
    
    def listar_marcas(self):
        """Lista todas as marcas disponíveis"""
        marcas = Marca.objects.all()
        print("\n" + "=" * 80)
        print("🏷️  MARCAS DISPONÍVEIS")
        print("=" * 80)
        for marca in marcas:
            count = ImagemProduto.objects.filter(produto__marca=marca).count()
            print(f"  ID {marca.id}: {marca.nome} ({count} imagens)")
        print()
        return marcas
    
    def listar_produtos(self, marca_id=None, categoria_id=None):
        """Lista produtos com filtros opcionais"""
        queryset = ProdutoMae.objects.all()
        
        if marca_id:
            queryset = queryset.filter(marca_id=marca_id)
        
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        
        print("\n" + "=" * 80)
        print("📦 PRODUTOS DISPONÍVEIS")
        print("=" * 80)
        
        for prod in queryset[:50]:
            count = ImagemProduto.objects.filter(produto=prod).count()
            print(f"  ID {prod.id}: {prod.descricao_produto[:50]}... ({count} imagens)")
        
        if queryset.count() > 50:
            print(f"  ... e mais {queryset.count() - 50} produtos")
        
        print()
        return queryset
    
    def processar_por_categoria(self, categoria_id, tipo_processamento='remover_fundo', apenas_nao_anotadas=True):
        """Processa todas as imagens de uma categoria"""
        print("\n" + "=" * 80)
        print(f"🎨 PROCESSANDO CATEGORIA {categoria_id}")
        print("=" * 80)
        
        queryset = ImagemProduto.objects.filter(produto__categoria_id=categoria_id)
        
        if apenas_nao_anotadas:
            anotadas = set()
            for img_anotada in ImagemAnotada.objects.all():
                anotadas.add(img_anotada.imagem)
            queryset = queryset.exclude(imagem__in=anotadas)
        
        caminhos = []
        for img in queryset:
            try:
                caminho = Path(f"media/{img.imagem}")
                if caminho.exists():
                    caminhos.append(str(caminho))
            except:
                pass
        
        print(f"📸 Total de imagens: {len(caminhos)}")
        
        if caminhos:
            resultados, erros = self.processador.processar_lote(
                tipo_processamento,
                caminhos,
                prefixo=f"cat_{categoria_id}"
            )
            
            self._mostrar_resultado(resultados, erros, tipo_processamento)
            self._registrar_processamento(resultados, erros, tipo_processamento)
        
        return len(caminhos)
    
    def processar_por_marca(self, marca_id, tipo_processamento='remover_fundo', apenas_nao_anotadas=True):
        """Processa todas as imagens de uma marca"""
        print("\n" + "=" * 80)
        print(f"🎨 PROCESSANDO MARCA {marca_id}")
        print("=" * 80)
        
        queryset = ImagemProduto.objects.filter(produto__marca_id=marca_id)
        
        if apenas_nao_anotadas:
            anotadas = set()
            for img_anotada in ImagemAnotada.objects.all():
                anotadas.add(img_anotada.imagem)
            queryset = queryset.exclude(imagem__in=anotadas)
        
        caminhos = []
        for img in queryset:
            try:
                caminho = Path(f"media/{img.imagem}")
                if caminho.exists():
                    caminhos.append(str(caminho))
            except:
                pass
        
        print(f"📸 Total de imagens: {len(caminhos)}")
        
        if caminhos:
            resultados, erros = self.processador.processar_lote(
                tipo_processamento,
                caminhos,
                prefixo=f"marca_{marca_id}"
            )
            
            self._mostrar_resultado(resultados, erros, tipo_processamento)
            self._registrar_processamento(resultados, erros, tipo_processamento)
        
        return len(caminhos)
    
    def processar_produto(self, produto_id, tipo_processamento='remover_fundo', apenas_nao_anotadas=True):
        """Processa todas as imagens de um produto"""
        produto = ProdutoMae.objects.get(id=produto_id)
        
        print("\n" + "=" * 80)
        print(f"🎨 PROCESSANDO PRODUTO: {produto.descricao_produto}")
        print("=" * 80)
        
        queryset = ImagemProduto.objects.filter(produto_id=produto_id)
        
        if apenas_nao_anotadas:
            anotadas = set()
            for img_anotada in ImagemAnotada.objects.all():
                anotadas.add(img_anotada.imagem)
            queryset = queryset.exclude(imagem__in=anotadas)
        
        caminhos = []
        for img in queryset:
            try:
                caminho = Path(f"media/{img.imagem}")
                if caminho.exists():
                    caminhos.append(str(caminho))
            except:
                pass
        
        print(f"📸 Total de imagens: {len(caminhos)}")
        
        if caminhos:
            resultados, erros = self.processador.processar_lote(
                tipo_processamento,
                caminhos,
                prefixo=f"prod_{produto_id}"
            )
            
            self._mostrar_resultado(resultados, erros, tipo_processamento)
            self._registrar_processamento(resultados, erros, tipo_processamento)
        
        return len(caminhos)
    
    def processar_multiplos_produtos(self, lista_ids, tipo_processamento='remover_fundo', apenas_nao_anotadas=True):
        """Processa imagens de múltiplos produtos"""
        print("\n" + "=" * 80)
        print(f"🎨 PROCESSANDO {len(lista_ids)} PRODUTOS")
        print("=" * 80)
        
        queryset = ImagemProduto.objects.filter(produto_id__in=lista_ids)
        
        if apenas_nao_anotadas:
            anotadas = set()
            for img_anotada in ImagemAnotada.objects.all():
                anotadas.add(img_anotada.imagem)
            queryset = queryset.exclude(imagem__in=anotadas)
        
        caminhos = []
        for img in queryset:
            try:
                caminho = Path(f"media/{img.imagem}")
                if caminho.exists():
                    caminhos.append(str(caminho))
            except:
                pass
        
        print(f"📸 Total de imagens: {len(caminhos)}")
        
        if caminhos:
            resultados, erros = self.processador.processar_lote(
                tipo_processamento,
                caminhos,
                prefixo="multi_prod"
            )
            
            self._mostrar_resultado(resultados, erros, tipo_processamento)
            self._registrar_processamento(resultados, erros, tipo_processamento)
        
        return len(caminhos)
    
    def processar_todas_nao_anotadas(self, tipo_processamento='remover_fundo'):
        """Processa TODAS as imagens que ainda não foram anotadas"""
        print("\n" + "=" * 80)
        print("🎨 PROCESSANDO TODAS AS IMAGENS NÃO ANOTADAS")
        print("=" * 80)
        
        # Obter imagens anotadas
        anotadas = set()
        for img_anotada in ImagemAnotada.objects.all():
            anotadas.add(img_anotada.imagem)
        
        print(f"📝 {len(anotadas)} imagens já foram anotadas")
        
        # Filtrar não anotadas
        queryset = ImagemProduto.objects.filter(ativa=True).exclude(imagem__in=anotadas)
        
        caminhos = []
        for img in queryset:
            try:
                caminho = Path(f"media/{img.imagem}")
                if caminho.exists():
                    caminhos.append(str(caminho))
            except:
                pass
        
        print(f"📸 Total de imagens não anotadas: {len(caminhos)}")
        
        if caminhos:
            resultados, erros = self.processador.processar_lote(
                tipo_processamento,
                caminhos,
                prefixo="todas"
            )
            
            self._mostrar_resultado(resultados, erros, tipo_processamento)
            self._registrar_processamento(resultados, erros, tipo_processamento)
        
        return len(caminhos)
    
    def _mostrar_resultado(self, resultados, erros, tipo):
        """Mostra resultado do processamento"""
        print()
        print("=" * 80)
        print(f"📊 RESULTADO - {tipo.upper()}")
        print("=" * 80)
        print(f"✅ Sucesso: {len(resultados)}")
        print(f"❌ Erros: {len(erros)}")
        
        if erros:
            print("\n⚠️  Erros:")
            for erro in erros[:10]:
                print(f"  • {erro['arquivo']}: {erro['erro'][:50]}")
            if len(erros) > 10:
                print(f"  ... e mais {len(erros) - 10} erros")
        
        if resultados:
            print(f"\n📁 Imagens processadas salvas em: media/produtos/processadas/")
            for result in resultados[:5]:
                print(f"  • {Path(result['processada']).name}")
            if len(resultados) > 5:
                print(f"  ... e mais {len(resultados) - 5} imagens")
        
        print()
    
    def _registrar_processamento(self, resultados, erros, tipo):
        """Registra processamento no banco de dados"""
        for result in resultados:
            ProcessadorImagensLog.objects.create(
                tipo=self._mapear_tipo(tipo),
                imagem_original=result['original'],
                imagem_processada=result['processada'],
                status='sucesso',
                parametros={}
            )
        
        for erro in erros:
            ProcessadorImagensLog.objects.create(
                tipo=self._mapear_tipo(tipo),
                imagem_original=erro['arquivo'],
                imagem_processada='',
                status='erro',
                mensagem_erro=erro['erro'],
                parametros={}
            )
    
    @staticmethod
    def _mapear_tipo(tipo_texto):
        """Mapeia nome de método para tipo no banco"""
        mapeamento = {
            'remover_fundo': 'remover_fundo',
            'redimensionar': 'redimensionar',
            'normalizar_cores': 'normalizar',
            'aumentar_contraste': 'aumentar_contraste',
        }
        return mapeamento.get(tipo_texto, 'remover_fundo')


def menu_interativo():
    """Menu interativo para processamento"""
    processador = ProcessadorEmLote()
    
    while True:
        print("\n" + "=" * 80)
        print("🎨 PROCESSADOR DE IMAGENS - MENU PRINCIPAL")
        print("=" * 80)
        print("\n1. Processar por CATEGORIA")
        print("2. Processar por MARCA")
        print("3. Processar um PRODUTO")
        print("4. Processar MÚLTIPLOS PRODUTOS")
        print("5. Processar TODAS as imagens NÃO anotadas")
        print("6. Listar Categorias")
        print("7. Listar Marcas")
        print("8. Listar Produtos")
        print("9. Sair")
        print()
        
        opcao = input("Escolha uma opção (1-9): ").strip()
        
        if opcao == '1':
            processador.listar_categorias()
            cat_id = input("Digite o ID da categoria: ").strip()
            if cat_id.isdigit():
                processador.processar_por_categoria(int(cat_id))
        
        elif opcao == '2':
            processador.listar_marcas()
            marca_id = input("Digite o ID da marca: ").strip()
            if marca_id.isdigit():
                processador.processar_por_marca(int(marca_id))
        
        elif opcao == '3':
            prod_id = input("Digite o ID do produto: ").strip()
            if prod_id.isdigit():
                processador.processar_produto(int(prod_id))
        
        elif opcao == '4':
            ids_texto = input("Digite os IDs separados por vírgula (ex: 1,2,3): ").strip()
            try:
                ids = [int(x.strip()) for x in ids_texto.split(',')]
                processador.processar_multiplos_produtos(ids)
            except:
                print("❌ IDs inválidos!")
        
        elif opcao == '5':
            processador.processar_todas_nao_anotadas()
        
        elif opcao == '6':
            processador.listar_categorias()
        
        elif opcao == '7':
            processador.listar_marcas()
        
        elif opcao == '8':
            processador.listar_produtos()
        
        elif opcao == '9':
            print("Até logo!")
            break
        
        else:
            print("❌ Opção inválida!")
        
        input("\nPressione ENTER para continuar...")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Modo linha de comando
        if sys.argv[1] == 'todas':
            ProcessadorEmLote().processar_todas_nao_anotadas()
            print("\n📸 Abrindo galeria...")
            os.system("python galeria_processadas.py")
        elif sys.argv[1] == 'categoria' and len(sys.argv) > 2:
            ProcessadorEmLote().processar_por_categoria(int(sys.argv[2]))
            print("\n📸 Abrindo galeria...")
            os.system("python galeria_processadas.py")
        elif sys.argv[1] == 'marca' and len(sys.argv) > 2:
            ProcessadorEmLote().processar_por_marca(int(sys.argv[2]))
            print("\n📸 Abrindo galeria...")
            os.system("python galeria_processadas.py")
        elif sys.argv[1] == 'produto' and len(sys.argv) > 2:
            ProcessadorEmLote().processar_produto(int(sys.argv[2]))
            print("\n📸 Abrindo galeria...")
            os.system("python galeria_processadas.py")
    else:
        # Menu interativo
        menu_interativo()
