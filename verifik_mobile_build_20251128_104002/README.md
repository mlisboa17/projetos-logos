# VerifiK Mobile - Build Package
    
## 📱 COMO COMPILAR O APK

### Opção 1: Google Colab (Recomendado)
1. Abra: https://colab.research.google.com
2. Faça upload destes arquivos
3. Execute o notebook de build
4. Download do APK gerado

### Opção 2: Linux/WSL
```bash
# Instalar dependências
sudo apt update
sudo apt install python3-pip git
pip3 install buildozer cython

# Compilar APK
buildozer android debug
```

## 📋 Arquivos inclusos:
- main.py (App Kivy principal)
- verifik.kv (Interface mobile)
- buildozer.spec (Configuração Android)
- mobile_simulator.db (Base com 176 produtos)

## 🎯 Resultado esperado:
- APK: bin/verifik_coleta-3.0.0-armeabi-v7a-debug.apk
- Tamanho: ~20-30 MB
- Compatibilidade: Android 4.1+

Criado em: 28/11/2025 às 10:40:02
