#!/usr/bin/env python3
"""
Executar scraper para todos os 11 postos com controle de progresso
"""
import os
import sys
import subprocess
import time

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')

def executar_scraper_todos_postos():
    """Executa scraper para todos os 11 postos"""
    
    print("🚀 INICIANDO COLETA DE DADOS REAIS DOS 11 POSTOS")
    print("="*60)
    
    # Lista dos 11 postos
    postos = [
        ('95406', 'AP CASA CAIADA'),
        ('107469', 'POSTO ENSEADA DO NOR'), 
        ('11236', 'POSTO REAL'),
        ('1153963', 'POSTO AVENIDA'),
        ('124282', 'R J'),
        ('14219', 'GLOBO105'),
        ('156075', 'POSTO BR SHOPPING'),
        ('1775869', 'POSTO DOZE'),
        ('5039', 'POSTO VIP'),
        ('61003', 'P IGARASSU'),
        ('94762', 'CIDADE PATRIMONIO')
    ]
    
    print(f"📋 Postos a processar: {len(postos)}")
    for codigo, nome in postos:
        print(f"   • {codigo} - {nome}")
    
    print(f"\n⏰ Tempo estimado: {len(postos) * 2} minutos")
    print("="*60)
    
    # Executar scraper
    try:
        cmd = [sys.executable, 'vibra_scraper.py']
        print(f"🔧 Comando: {' '.join(cmd)}")
        print("⏳ Executando... (Aguarde)")
        
        # Executar com output em tempo real
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Mostrar output em tempo real
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        # Verificar resultado
        return_code = process.poll()
        
        if return_code == 0:
            print("\n" + "="*60)
            print("🎉 SCRAPING CONCLUÍDO COM SUCESSO!")
            print("✅ Dados de todos os 11 postos coletados")
            print("✅ Dashboard atualizado automaticamente")
            print("="*60)
            return True
        else:
            print(f"\n❌ ERRO: Processo terminou com código {return_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        return False

if __name__ == "__main__":
    executar_scraper_todos_postos()