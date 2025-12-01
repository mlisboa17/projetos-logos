#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from logos.models import Categoria, ImagemProduto

print("=" * 60)
print("CATEGORIAS DISPONÍVEIS NO BANCO")
print("=" * 60)

categorias = Categoria.objects.all()
print(f"\nTotal de categorias: {categorias.count()}\n")

for c in categorias:
    count = ImagemProduto.objects.filter(produto__categoria=c).count()
    print(f"ID: {c.id:2} | Nome: {c.nome:30} | Imagens: {count}")

print("\n" + "=" * 60)
print(f"Total de imagens no sistema: {ImagemProduto.objects.count()}")
print("=" * 60)
