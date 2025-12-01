import os
print("Teste Python: OK")

caminho = r"C:\Users\gabri\Downloads\WhatsApp Image 2025-11-30 at 22.25.20.jpeg"
if os.path.exists(caminho):
    print(f"Arquivo: OK - {os.path.getsize(caminho)} bytes")
else:
    print("Arquivo: ERRO - não encontrado")

print("Diretório atual:", os.getcwd())
print("Arquivos Python:", [f for f in os.listdir('.') if f.endswith('.py')][:5])