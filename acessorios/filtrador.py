"""
Filtrador de Imagens
Permite filtrar imagens por múltiplos critérios
"""
from pathlib import Path
from django.db.models import Q


class FiltrorImagens:
    """Classe para filtrar imagens de forma genérica"""
    
    def __init__(self, modelo_imagem=None):
        """
        modelo_imagem: Modelo Django a usar (ex: ImagemProduto)
        """
        self.modelo = modelo_imagem
        self.queryset = None
        
    def por_categoria(self, categoria_id):
        """Filtra imagens por categoria"""
        if self.queryset is None and self.modelo:
            self.queryset = self.modelo.objects.all()
        
        if self.queryset is not None:
            return self.queryset.filter(
                produto__categoria_id=categoria_id
            )
        return None
    
    def por_produto(self, produto_id):
        """Filtra imagens por um produto específico"""
        if self.queryset is None and self.modelo:
            self.queryset = self.modelo.objects.all()
        
        if self.queryset is not None:
            return self.queryset.filter(
                produto_id=produto_id
            )
        return None
    
    def por_multiplos_produtos(self, lista_produto_ids):
        """Filtra imagens por múltiplos produtos"""
        if self.queryset is None and self.modelo:
            self.queryset = self.modelo.objects.all()
        
        if self.queryset is not None:
            return self.queryset.filter(
                produto_id__in=lista_produto_ids
            )
        return None
    
    def por_marca(self, marca_id):
        """Filtra imagens por marca"""
        if self.queryset is None and self.modelo:
            self.queryset = self.modelo.objects.all()
        
        if self.queryset is not None:
            return self.queryset.filter(
                produto__marca_id=marca_id
            )
        return None
    
    def por_status(self, status):
        """Filtra imagens por status (ativa/inativa)"""
        if self.queryset is None and self.modelo:
            self.queryset = self.modelo.objects.all()
        
        if self.queryset is not None:
            return self.queryset.filter(
                ativa=(status == 'ativa')
            )
        return None
    
    def nao_anotadas(self, modelo_anotacoes):
        """Filtra imagens que ainda não foram anotadas"""
        if self.queryset is None and self.modelo:
            self.queryset = self.modelo.objects.all()
        
        if self.queryset is not None:
            # Obter IDs de imagens já anotadas
            anotadas = set()
            for img_anotada in modelo_anotacoes.objects.all():
                anotadas.add(img_anotada.imagem)
            
            # Filtrar
            return self.queryset.exclude(
                imagem__in=anotadas
            )
        return None
    
    def por_tamanho(self, tamanho_minimo_kb=100):
        """Filtra imagens por tamanho mínimo"""
        if self.queryset is None and self.modelo:
            self.queryset = self.modelo.objects.all()
        
        resultados = []
        if self.queryset is not None:
            for img in self.queryset:
                try:
                    caminho = Path(f"media/{img.imagem}")
                    if caminho.exists():
                        tamanho_kb = caminho.stat().st_size / 1024
                        if tamanho_kb >= tamanho_minimo_kb:
                            resultados.append(img)
                except:
                    pass
        
        return resultados
    
    def obter_caminhos(self, queryset=None):
        """Obter lista de caminhos de arquivos"""
        if queryset is None:
            queryset = self.queryset
        
        if queryset is None:
            return []
        
        caminhos = []
        for img in queryset:
            try:
                caminho = Path(f"media/{img.imagem}")
                if caminho.exists():
                    caminhos.append(str(caminho))
            except:
                pass
        
        return caminhos
    
    @staticmethod
    def aplicar_multiplos_filtros(queryset, **filtros):
        """
        Aplica múltiplos filtros de uma vez
        
        Exemplo:
        filtros = {
            'categoria': 5,
            'marca': 2,
            'ativa': True,
        }
        """
        if 'categoria' in filtros and filtros['categoria']:
            queryset = queryset.filter(produto__categoria_id=filtros['categoria'])
        
        if 'marca' in filtros and filtros['marca']:
            queryset = queryset.filter(produto__marca_id=filtros['marca'])
        
        if 'produto' in filtros and filtros['produto']:
            queryset = queryset.filter(produto_id=filtros['produto'])
        
        if 'produtos' in filtros and filtros['produtos']:
            queryset = queryset.filter(produto_id__in=filtros['produtos'])
        
        if 'ativa' in filtros and filtros['ativa'] is not None:
            queryset = queryset.filter(ativa=filtros['ativa'])
        
        return queryset
