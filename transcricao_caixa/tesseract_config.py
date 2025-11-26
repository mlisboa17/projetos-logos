"""
Configuração do Tesseract OCR
Define o caminho do executável automaticamente
"""
import os
import pytesseract

# Detectar caminho do Tesseract automaticamente
TESSERACT_PATHS = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    r'/usr/bin/tesseract',
    r'/usr/local/bin/tesseract',
]

def configurar_tesseract():
    """Configura o caminho do Tesseract automaticamente"""
    for path in TESSERACT_PATHS:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return True
    return False

# Configurar automaticamente ao importar
configurar_tesseract()
