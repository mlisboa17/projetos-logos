#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Ler o arquivo
with open('verifik/models_anotacao.py', 'r', encoding='utf-8') as f:
    conteudo = f.read()

# Adicionar o novo modelo no final
novo_modelo = '''

class ImagemProcessada(models.Model):
    """Imagens processadas com fundo removido vinculadas às imagens originais"""
    from verifik.models import ImagemProduto
    
    imagem_original = models.ForeignKey(ImagemProduto, on_delete=models.CASCADE, related_name='imagens_processadas')
    imagem_processada = models.ImageField(upload_to='processadas_sem_fundo/')
    tipo_processamento = models.CharField(max_length=50, default='fundo_removido')
    descricao = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Imagem Processada'
        verbose_name_plural = 'Imagens Processadas'
        ordering = ['-data_criacao']

    def __str__(self):
        return f'{self.imagem_original.produto.descricao_produto} - {self.tipo_processamento}'
'''

# Escrever de volta
with open('verifik/models_anotacao.py', 'w', encoding='utf-8') as f:
    f.write(conteudo + novo_modelo)

print("✅ Modelo ImagemProcessada adicionado com sucesso!")
