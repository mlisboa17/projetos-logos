#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Ler o arquivo
with open('verifik/models.py', 'r', encoding='utf-8') as f:
    conteudo = f.read()

# Adicionar o novo modelo no final
novo_modelo = '''

class ImagemAnotada(models.Model):
    """Imagens processadas com fundo removido vinculadas às imagens originais"""
    imagem_original = models.OneToOneField(ImagemProduto, on_delete=models.CASCADE, related_name='imagem_processada')
    imagem_anotada = models.ImageField(upload_to='processadas_sem_fundo/')
    tipo_anotacao = models.CharField(max_length=50, default='fundo_removido')
    descricao = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Imagem Anotada'
        verbose_name_plural = 'Imagens Anotadas'
        ordering = ['-data_criacao']

    def __str__(self):
        return f'{self.imagem_original.produto.descricao_produto} - {self.tipo_anotacao}'
'''

# Escrever de volta
with open('verifik/models.py', 'w', encoding='utf-8') as f:
    f.write(conteudo + novo_modelo)

print("✅ Modelo ImagemAnotada adicionado com sucesso!")
