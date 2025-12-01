print("Hello World!")
print("Teste funcionando")

import os
print(f"Diretório atual: {os.getcwd()}")

# Teste de arquivo
caminho = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
if os.path.exists(caminho):
    print("✅ Arquivo encontrado")
    print(f"Tamanho: {os.path.getsize(caminho)} bytes")
else:
    print("❌ Arquivo não encontrado")