# Script para criar executável do Sistema de Coleta
# Gera um arquivo .exe que pode ser copiado para outras máquinas

import PyInstaller.__main__
import os

# Configurações
script_name = 'sistema_coleta_standalone.py'
exe_name = 'VerifiK_ColetaImagens'
icon_path = None  # Opcional: caminho para um ícone .ico

# Argumentos do PyInstaller
args = [
    script_name,
    '--name=' + exe_name,
    '--onefile',  # Um único arquivo executável
    '--windowed',  # Sem console (apenas GUI)
    '--clean',
    '--noconfirm',
]

if icon_path and os.path.exists(icon_path):
    args.append(f'--icon={icon_path}')

# Adicionar dados necessários
args.extend([
    '--add-data=README_SISTEMA_COLETA.txt;.',
])

print("🔨 Criando executável...")
print("=" * 50)

PyInstaller.__main__.run(args)

print("\n✅ Executável criado com sucesso!")
print("📁 Localização: dist/" + exe_name + ".exe")
print("\n📋 Instruções:")
print("1. Copie o arquivo .exe da pasta 'dist' para um pendrive")
print("2. Leve para outras máquinas")
print("3. Execute o programa (não precisa instalar nada!)")
print("4. Quando terminar, use 'Exportar para Sincronização'")
print("5. Traga a pasta exportada de volta")
print("6. Use o script importar_dados_coletados.py para sincronizar")
