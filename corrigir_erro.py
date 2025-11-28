"""
Corrigir erro do ttkbootstrap - remover e manter Tkinter padrão
"""

with open('sistema_coleta_standalone_v2.py', 'r', encoding='utf-8') as f:
    codigo = f.read()

# Remover imports do ttkbootstrap
codigo = codigo.replace('import ttkbootstrap as ttk\nfrom ttkbootstrap.constants import *', 'from tkinter import ttk')
codigo = codigo.replace('from ttkbootstrap.constants import *', '')

# Remover linha do style
codigo = codigo.replace("        self.root.style = ttk.Style(theme='cosmo')\n", '')

# Remover qualquer referência a ttkbootstrap que sobrou
codigo = codigo.replace('import ttkbootstrap', '')
codigo = codigo.replace('ttkbootstrap', 'ttk')

# Salvar
with open('sistema_coleta_standalone_v2.py', 'w', encoding='utf-8') as f:
    f.write(codigo)

print("✅ Código corrigido!")
print("✅ ttkbootstrap removido")
print("✅ Sistema voltou para Tkinter padrão")
print("\nO sistema continua com todas as melhorias:")
print("- Instruções passo a passo")
print("- Mensagens amigáveis")
print("- Sincronização automática")
print("- Interface responsiva")
