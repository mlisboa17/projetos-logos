"""
Instruções para configurar Google Drive como servidor do banco de dados
"""

print("="*70)
print("📁 CONFIGURAR GOOGLE DRIVE PARA DOWNLOAD DIRETO")
print("="*70)

print("""
PASSO A PASSO:

1️⃣ FAZER UPLOAD DO BANCO:
   - Acesse: https://drive.google.com
   - Faça upload do arquivo: db.sqlite3
   
2️⃣ COMPARTILHAR ARQUIVO:
   - Clique com botão direito no arquivo
   - Selecione "Compartilhar"
   - Clique em "Alterar" ao lado de "Restrito"
   - Selecione "Qualquer pessoa com o link"
   - Clique em "Concluído"

3️⃣ COPIAR LINK:
   - Clique com botão direito → "Obter link"
   - Você receberá algo como:
     https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/view?usp=sharing

4️⃣ CONVERTER PARA DOWNLOAD DIRETO:
   Link original:
   https://drive.google.com/file/d/FILE_ID/view?usp=sharing
   
   Link de download direto:
   https://drive.google.com/uc?export=download&id=FILE_ID
   
   Exemplo:
   Original: https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/view?usp=sharing
   Direto:   https://drive.google.com/uc?export=download&id=1AbCdEfGhIjKlMnOpQrStUvWxYz

5️⃣ USAR NO SISTEMA:
   LINK_ONEDRIVE_BANCO = "https://drive.google.com/uc?export=download&id=FILE_ID"

""")

print("="*70)
print("💡 VANTAGENS DO GOOGLE DRIVE:")
print("="*70)
print("""
✅ Funciona de qualquer lugar (internet)
✅ Download direto sem conversão complicada
✅ Atualização automática quando substituir arquivo
✅ Gratuito até 15 GB
✅ Mais rápido que OneDrive
✅ Sem necessidade de servidor rodando
""")

print("="*70)
print("⚠️ IMPORTANTE:")
print("="*70)
print("""
- Sempre que atualizar o banco, SUBSTITUA o arquivo no Google Drive
- O link permanece o mesmo
- Funcionários baixam versão mais recente automaticamente
""")

print("="*70)
