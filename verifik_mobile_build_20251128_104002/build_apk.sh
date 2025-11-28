#!/bin/bash

echo "Compilando VerifiK Mobile APK..."
echo "Versao: 3.0.0"
echo ""

# Verificar buildozer
if ! command -v buildozer &> /dev/null; then
    echo "Buildozer nao encontrado. Instalando..."
    pip3 install buildozer cython
fi

# Limpar builds anteriores
echo "Limpando builds anteriores..."
rm -rf .buildozer
rm -rf bin

# Compilar APK
echo "Iniciando compilacao..."
buildozer android debug

# Verificar resultado
if [ -f "bin/*.apk" ]; then
    echo "APK compilado com sucesso!"
    ls -la bin/
else
    echo "Erro na compilacao"
    exit 1
fi

echo ""
echo "VerifiK Mobile APK esta pronto!"
echo "Instale no Android e teste a coleta de imagens."
