"""
Teste do Sistema de Coleta de Imagens em resolução 1360x768
"""

import tkinter as tk
import sys
import os

# Adicionar o diretório atual ao path para importar o sistema
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sistema_coleta_standalone_v2 import SistemaColetaImagens

def main():
    root = tk.Tk()
    
    # Simular resolução 1360x768
    root.wm_maxsize(1360, 768)
    root.geometry("1350x760+5+5")  # Deixar um pouco de margem
    
    # Sobrescrever métodos de detecção de tela para simular resolução baixa
    original_screenwidth = root.winfo_screenwidth
    original_screenheight = root.winfo_screenheight
    
    def mock_screenwidth():
        return 1360
    
    def mock_screenheight():
        return 768
    
    root.winfo_screenwidth = mock_screenwidth
    root.winfo_screenheight = mock_screenheight
    
    print("🔧 TESTE: Simulando resolução 1360x768")
    print("📱 Verificando se os botões ficam visíveis...")
    
    app = SistemaColetaImagens(root)
    
    # Restaurar métodos originais após criação da interface
    root.winfo_screenwidth = original_screenwidth
    root.winfo_screenheight = original_screenheight
    
    root.mainloop()

if __name__ == '__main__':
    main()