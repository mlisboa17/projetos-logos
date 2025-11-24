# -*- coding: utf-8 -*-
"""Remove emojis do scraper"""

arquivo = 'fuel_prices/scrapers/vibra_scraper.py'

with open(arquivo, 'r', encoding='utf-8') as f:
    content = f.read()

# Substituir emojis por texto
content = content.replace('🔍', '[INFO]')
content = content.replace('🔐', '[LOGIN]')
content = content.replace('⚠️', '[WARN]')
content = content.replace('🎯', '[TARGET]')
content = content.replace('🔄', '[SWITCH]')
content = content.replace('💾', '[SAVE]')
content = content.replace('📊', '[STATS]')
content = content.replace('✅', '[OK]')
content = content.replace('❌', '[ERROR]')
content = content.replace('🚀', '[START]')
content = content.replace('📂', '[FILE]')
content = content.replace('🏪', '[POSTO]')
content = content.replace('⏱️', '[TIME]')
content = content.replace('📁', '[FOLDER]')

with open(arquivo, 'w', encoding='utf-8') as f:
    f.write(content)

print("Emojis removidos com sucesso!")
