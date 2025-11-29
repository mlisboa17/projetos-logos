#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para verificar ambiente Python e dependências do projeto
"""

import sys
import platform
import subprocess

def check_import(package_name, import_name=None):
    """Verifica se um pacote pode ser importado"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        return True, "✓"
    except ImportError as e:
        return False, f"✗ ({str(e)})"

def get_package_version(package_name):
    """Obtém versão de um pacote instalado"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        for line in result.stdout.split('\n'):
            if line.startswith('Version:'):
                return line.split(':', 1)[1].strip()
    except:
        pass
    return "?"

def main():
    print("=" * 70)
    print("VERIFICAÇÃO DO AMBIENTE PYTHON")
    print("=" * 70)
    print()
    
    # Informações do sistema
    print("📊 INFORMAÇÕES DO SISTEMA")
    print("-" * 70)
    print(f"Sistema Operacional: {platform.system()} {platform.release()}")
    print(f"Arquitetura: {platform.machine()}")
    print(f"Python: {sys.version}")
    print(f"Executável: {sys.executable}")
    print()
    
    # Dependências principais
    print("📦 DEPENDÊNCIAS PRINCIPAIS")
    print("-" * 70)
    
    packages = [
        ("Django", "django"),
        ("Pillow (PIL)", "PIL"),
        ("OpenCV", "cv2"),
        ("NumPy", "numpy"),
        ("Ultralytics (YOLO)", "ultralytics"),
        ("PyYAML", "yaml"),
        ("Torch", "torch"),
    ]
    
    for display_name, import_name in packages:
        status, msg = check_import(import_name.split('.')[0])
        version = get_package_version(import_name.split('.')[0])
        
        if status:
            print(f"{msg} {display_name:<30} (versão: {version})")
        else:
            print(f"{msg} {display_name:<30} NÃO INSTALADO")
    
    print()
    
    # Data Augmentation
    print("🎨 DATA AUGMENTATION")
    print("-" * 70)
    
    albu_status, albu_msg = check_import("albumentations")
    albu_version = get_package_version("albumentations")
    
    if albu_status:
        print(f"✓ Albumentations instalado (versão: {albu_version})")
        print(f"  └─ Disponível: augmentação completa com 10 transformações")
        print(f"  └─ Multiplicador: 8x (1 original + 7 augmentações)")
    else:
        print(f"✗ Albumentations NÃO instalado")
        print(f"  └─ Motivo: {albu_msg}")
        print(f"  └─ Status atual: Treinamento simplificado (sem augmentation)")
        print(f"  └─ Impacto: Menor diversidade de dados de treino")
    
    print()
    
    # Compilador C++
    print("🔧 COMPILADOR C++ (para Albumentations)")
    print("-" * 70)
    
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ["where", "cl.exe"],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0:
                print("✓ Microsoft Visual C++ Compiler encontrado")
                print(f"  └─ Localização: {result.stdout.strip()}")
            else:
                print("✗ Microsoft Visual C++ Compiler NÃO encontrado")
                print("  └─ Necessário para compilar dependências do Albumentations")
                print("  └─ Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
        except:
            print("✗ Não foi possível verificar compilador C++")
    else:
        print("ℹ Verificação de compilador disponível apenas para Windows")
    
    print()
    
    # Django Apps
    print("🌐 DJANGO CONFIGURATION")
    print("-" * 70)
    
    try:
        import os
        import django
        
        # Configurar Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
        django.setup()
        
        from django.conf import settings
        
        installed_apps = settings.INSTALLED_APPS
        print(f"✓ Django configurado (settings: logos.settings)")
        
        if 'verifik' in installed_apps or 'fuel_prices.verifik' in installed_apps:
            print(f"  ✓ App 'verifik' em INSTALLED_APPS")
        else:
            print(f"  ✗ App 'verifik' NÃO está em INSTALLED_APPS")
            print(f"    └─ Comandos Django não serão reconhecidos")
        
        # Verificar modelos
        from fuel_prices.verifik.models import ImagemProduto
        
        total_imagens = ImagemProduto.objects.count()
        imagens_treinadas = ImagemProduto.objects.filter(treinada=True).count()
        imagens_novas = ImagemProduto.objects.filter(treinada=False).count()
        
        print(f"  └─ Total de imagens: {total_imagens}")
        print(f"  └─ Imagens treinadas: {imagens_treinadas}")
        print(f"  └─ Imagens novas: {imagens_novas}")
        
    except Exception as e:
        print(f"✗ Erro ao verificar Django: {e}")
    
    print()
    
    # Checkpoint YOLO
    print("🤖 MODELO YOLO")
    print("-" * 70)
    
    checkpoint_paths = [
        r"C:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\fuel_prices\runs\detect\heineken_330ml\weights\last.pt",
        r"fuel_prices\runs\detect\heineken_330ml\weights\last.pt",
        r"runs\detect\heineken_330ml\weights\last.pt",
    ]
    
    checkpoint_found = False
    for path in checkpoint_paths:
        if os.path.exists(path):
            print(f"✓ Checkpoint encontrado: {path}")
            
            # Tentar carregar informações
            try:
                from ultralytics import YOLO
                model = YOLO(path)
                print(f"  └─ Modelo carregado com sucesso")
                checkpoint_found = True
                break
            except Exception as e:
                print(f"  └─ Erro ao carregar: {e}")
    
    if not checkpoint_found:
        print("✗ Checkpoint não encontrado nas localizações padrão")
        print("  └─ Treinamento iniciará do zero")
    
    print()
    
    # Recomendações
    print("💡 RECOMENDAÇÕES")
    print("-" * 70)
    
    if not albu_status:
        print("1. INSTALAR ALBUMENTATIONS:")
        print("   - Instale Visual Studio Build Tools")
        print("   - Execute: pip install albumentations")
        print("   - OU use: conda install -c conda-forge albumentations")
        print()
    
    if 'verifik' not in installed_apps and 'fuel_prices.verifik' not in installed_apps:
        print("2. ADICIONAR VERIFIK AO INSTALLED_APPS:")
        print("   - Edite: logos/settings.py")
        print("   - Adicione 'fuel_prices.verifik' em INSTALLED_APPS")
        print()
    
    print("3. SCRIPTS DISPONÍVEIS:")
    print("   - treinar_simples.py: Treinamento sem augmentation (atual)")
    print("   - manage.py treinar_incremental: Com augmentation (requer albumentations)")
    print("   - verificar_ambiente.py: Este script")
    
    print()
    print("=" * 70)
    print("Verificação concluída!")
    print("=" * 70)

if __name__ == "__main__":
    main()
