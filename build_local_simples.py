#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BUILD LOCAL SIMPLIFICADO - VerifiK Mobile APK
Para quando o GitHub Actions não funciona
"""

import os
import subprocess
import sys
import platform

def verificar_sistema():
    """Verifica se o sistema suporta build local"""
    print("🔍 VERIFICANDO SISTEMA PARA BUILD LOCAL\n")
    
    sistema = platform.system()
    print(f"Sistema operacional: {sistema}")
    
    if sistema == "Windows":
        print("✅ Windows detectado")
        print("📋 OPÇÕES DISPONÍVEIS:")
        print("   1. WSL Ubuntu (recomendado)")
        print("   2. Docker Desktop")
        print("   3. Máquina Virtual Linux")
        print("   4. Google Colab (online)")
        return "windows"
    
    elif sistema == "Linux":
        print("✅ Linux detectado - PERFEITO para build!")
        return "linux"
    
    elif sistema == "Darwin":
        print("✅ macOS detectado")
        print("📋 Buildozer funciona no macOS com algumas limitações")
        return "macos"
    
    return sistema.lower()

def instalar_dependencias_linux():
    """Instala dependências no Linux"""
    print("\n🔧 INSTALANDO DEPENDÊNCIAS LINUX...\n")
    
    comandos = [
        "sudo apt update",
        "sudo apt install -y python3-pip git zip unzip",
        "sudo apt install -y openjdk-11-jdk",
        "sudo apt install -y build-essential libffi-dev libssl-dev",
        "pip3 install --upgrade pip",
        "pip3 install buildozer cython kivy[base] pyjnius plyer"
    ]
    
    for cmd in comandos:
        print(f"Executando: {cmd}")
        try:
            resultado = subprocess.run(cmd.split(), capture_output=True, text=True)
            if resultado.returncode == 0:
                print("✅ Sucesso")
            else:
                print(f"⚠️ Aviso: {resultado.stderr}")
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    # Configurar JAVA_HOME
    java_home = "/usr/lib/jvm/java-11-openjdk-amd64"
    print(f"\n🔧 Configurando JAVA_HOME: {java_home}")
    
    os.environ['JAVA_HOME'] = java_home
    os.environ['PATH'] = f"{os.environ['PATH']}:{java_home}/bin"

def compilar_apk():
    """Compila o APK"""
    print("\n🚀 INICIANDO COMPILAÇÃO DO APK...\n")
    
    # Verificar arquivos necessários
    arquivos_necessarios = ['main.py', 'verifik.kv', 'buildozer.spec']
    
    for arquivo in arquivos_necessarios:
        if not os.path.exists(arquivo):
            print(f"❌ Arquivo não encontrado: {arquivo}")
            return False
    
    print("✅ Todos os arquivos encontrados")
    
    # Limpar builds anteriores
    print("🧹 Limpando builds anteriores...")
    if os.path.exists('.buildozer'):
        subprocess.run(['rm', '-rf', '.buildozer'])
    if os.path.exists('bin'):
        subprocess.run(['rm', '-rf', 'bin'])
    
    # Compilar
    print("⚡ Compilando APK (pode demorar 10-20 minutos)...")
    print("📊 Progresso será mostrado abaixo:")
    print("-" * 50)
    
    try:
        processo = subprocess.Popen(
            ['buildozer', 'android', 'debug'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Mostrar saída em tempo real
        while True:
            linha = processo.stdout.readline()
            if not linha and processo.poll() is not None:
                break
            if linha:
                print(linha.strip())
        
        codigo_retorno = processo.poll()
        
        if codigo_retorno == 0:
            print("\n✅ COMPILAÇÃO CONCLUÍDA COM SUCESSO!")
            
            # Procurar APK gerado
            import glob
            apks = glob.glob("bin/*.apk")
            if apks:
                apk_file = apks[0]
                tamanho = os.path.getsize(apk_file) / (1024*1024)
                print(f"📱 APK gerado: {apk_file}")
                print(f"📊 Tamanho: {tamanho:.1f} MB")
                
                # Renomear para nome mais amigável
                novo_nome = "VerifiK_Mobile_v3.0.0.apk"
                os.rename(apk_file, novo_nome)
                print(f"📱 APK renomeado para: {novo_nome}")
                
                return True
        else:
            print(f"\n❌ ERRO NA COMPILAÇÃO (código: {codigo_retorno})")
            return False
            
    except Exception as e:
        print(f"\n❌ ERRO DURANTE COMPILAÇÃO: {e}")
        return False

def guia_wsl_windows():
    """Guia para usar WSL no Windows"""
    print("\n📋 GUIA WSL PARA WINDOWS:\n")
    
    print("1️⃣ INSTALAR WSL (PowerShell como Admin):")
    print("   wsl --install")
    print("   wsl --install -d Ubuntu")
    print()
    
    print("2️⃣ ENTRAR NO WSL:")
    print("   wsl")
    print()
    
    print("3️⃣ NAVEGAR PARA O PROJETO:")
    print("   cd /mnt/c/Users/mlisb/OneDrive/Desktop/ProjetoLogus")
    print()
    
    print("4️⃣ EXECUTAR ESTE SCRIPT:")
    print("   python3 build_local_simples.py")
    print()
    
    print("5️⃣ AGUARDAR COMPILAÇÃO (10-20 min)")
    print()
    
    print("6️⃣ COPIAR APK PARA WINDOWS:")
    print("   cp VerifiK_Mobile_v3.0.0.apk /mnt/c/Users/mlisb/Desktop/")

def main():
    """Função principal"""
    print("📱 BUILD LOCAL SIMPLIFICADO - VerifiK Mobile")
    print("=" * 50)
    
    sistema = verificar_sistema()
    
    if sistema == "linux":
        print("\n🎉 SISTEMA LINUX - PRONTO PARA BUILD!")
        
        resposta = input("\nDeseja instalar dependências? (s/N): ").lower()
        if resposta in ['s', 'sim', 'y', 'yes']:
            instalar_dependencias_linux()
        
        resposta = input("\nDeseja compilar o APK agora? (s/N): ").lower()
        if resposta in ['s', 'sim', 'y', 'yes']:
            if compilar_apk():
                print("\n🎉 APK PRONTO PARA INSTALAÇÃO NO ANDROID!")
                print("📱 Transfira o arquivo VerifiK_Mobile_v3.0.0.apk para o celular")
                print("⚙️ Habilite 'Fontes desconhecidas' nas configurações Android")
                print("📲 Instale o APK e teste o VerifiK Mobile!")
    
    elif sistema == "windows":
        print("\n⚠️ SISTEMA WINDOWS - PRECISA DO WSL")
        guia_wsl_windows()
        
        print("\n💡 ALTERNATIVAS SEM WSL:")
        print("   🌐 Google Colab: https://colab.research.google.com")
        print("   📦 Docker Desktop + container Linux")
        print("   💻 Máquina virtual Ubuntu")
    
    else:
        print(f"\n❓ Sistema {sistema} - verificar compatibilidade com Buildozer")

if __name__ == "__main__":
    main()