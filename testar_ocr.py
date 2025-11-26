"""
Script de teste para OCR Tesseract
Cria uma imagem de teste e processa com OCR
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from transcricao_caixa.ocr_processor import TesseractOCRProcessor, testar_tesseract
from PIL import Image, ImageDraw, ImageFont

print("="*70)
print("TESTE DO OCR TESSERACT")
print("="*70)

# Testar se Tesseract está instalado
print("\n1. Testando Tesseract...")
sucesso, mensagem = testar_tesseract()
print(f"   {mensagem}")

if not sucesso:
    print("\n❌ Tesseract não está configurado corretamente!")
    sys.exit(1)

# Criar imagem de teste
print("\n2. Criando imagem de teste...")
img = Image.new('RGB', (800, 500), 'white')
draw = ImageDraw.Draw(img)

# Desenhar borda
draw.rectangle([40, 40, 760, 460], outline='black', width=3)

# Adicionar texto
try:
    # Tentar usar fonte maior
    font = ImageFont.truetype("arial.ttf", 20)
except:
    font = ImageFont.load_default()

draw.text((60, 60), 'NOTA FISCAL ELETRÔNICA', fill='black', font=font)
draw.text((60, 120), 'NF-e: 123456', fill='black', font=font)
draw.text((60, 180), 'Data: 26/11/2025', fill='black', font=font)
draw.text((60, 240), 'Valor Total: R$ 1.234,56', fill='black', font=font)
draw.text((60, 300), 'CNPJ: 12.345.678/0001-90', fill='black', font=font)
draw.text((60, 360), 'Cliente: João da Silva', fill='black', font=font)

img.save('teste_nf.png')
print("   ✓ Imagem salva: teste_nf.png")

# Processar com OCR
print("\n3. Processando imagem com OCR...")
ocr = TesseractOCRProcessor()
resultado = ocr.processar_documento_completo('teste_nf.png')

print("\n" + "="*70)
print("RESULTADO DO OCR")
print("="*70)

if resultado['sucesso']:
    print(f"\n✓ Processamento bem-sucedido!")
    print(f"  Confiança: {resultado['confianca']}%")
    
    print(f"\n📄 TEXTO EXTRAÍDO:")
    print("-"*70)
    print(resultado['texto'])
    print("-"*70)
    
    print(f"\n📊 DADOS ESTRUTURADOS:")
    dados = resultado['dados_extraidos']
    print(f"  💰 Valor Total: R$ {dados['valor_total']:.2f}")
    print(f"  📋 Número NF: {dados['numero_documento']}")
    print(f"  📅 Data: {dados['data_documento']}")
    
    if dados['valores_encontrados']:
        print(f"\n  💵 Todos os valores encontrados:")
        for v in dados['valores_encontrados']:
            print(f"     - R$ {v:.2f}")
    
    if dados['datas_encontradas']:
        print(f"\n  📆 Todas as datas encontradas:")
        for d in dados['datas_encontradas']:
            print(f"     - {d}")
    
    if dados['numeros_encontrados']:
        print(f"\n  🔢 Números de documento encontrados:")
        for n in dados['numeros_encontrados']:
            print(f"     - {n}")
    
    print("\n" + "="*70)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    print("="*70)
    
else:
    print(f"\n❌ Erro no processamento:")
    print(f"   {resultado['erro']}")
    print("\n" + "="*70)
    print("❌ TESTE FALHOU")
    print("="*70)

print("\n💡 Dica: Abra o arquivo 'teste_nf.png' para ver a imagem de teste")
