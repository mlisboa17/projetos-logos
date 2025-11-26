╔══════════════════════════════════════════════════════════════════╗
║    SISTEMA DE COLETA DE IMAGENS - VerifiK (Versão Standalone)   ║
╚══════════════════════════════════════════════════════════════════╝

📸 O QUE É ESTE SISTEMA?
------------------------
Sistema OFFLINE para funcionários coletarem fotos de produtos e
marcarem onde cada produto aparece usando bounding boxes.

Não precisa de internet ou instalação de programas adicionais!


🎯 FUNCIONALIDADES
------------------
1. ✅ Adicionar novos produtos ao catálogo
2. ✅ Carregar fotos do computador
3. ✅ Tirar fotos com webcam
4. ✅ Desenhar bounding boxes (clique e arraste)
5. ✅ Marcar múltiplos produtos na mesma foto
6. ✅ Salvar anotações localmente
7. ✅ Exportar dados para sincronização


📋 COMO USAR
------------

PASSO 1: ADICIONAR PRODUTOS
   - Clique em "➕ Adicionar Novo Produto"
   - Digite a DESCRIÇÃO COMPLETA (ex: "Coca-Cola 350ml Lata")
   - Digite a marca (opcional)
   - Clique em "Salvar"

PASSO 2: CARREGAR/TIRAR FOTO
   - Opção A: Clique em "📁 Carregar Imagem" e escolha uma foto
   - Opção B: Clique em "📷 Tirar Foto" para usar a webcam

PASSO 3: ANOTAR PRODUTOS
   - Selecione um produto na lista da esquerda
   - Clique e arraste na imagem para desenhar um retângulo ao redor do produto
   - Repita para cada produto que aparece na foto
   - Dica: Use a busca para encontrar produtos rapidamente

PASSO 4: SALVAR
   - Adicione observações se necessário
   - Clique em "💾 Salvar Anotações"
   - O sistema salvará tudo automaticamente

PASSO 5: EXPORTAR (no final do dia)
   - Clique em "📤 Exportar para Sincronização"
   - Escolha uma pasta (ex: Desktop)
   - Uma pasta será criada com todos os dados
   - Copie esta pasta para um pendrive


💾 ONDE OS DADOS SÃO SALVOS?
-----------------------------
Todos os dados ficam na pasta "dados_coleta" ao lado do programa:

dados_coleta/
  ├── coleta.db          (banco de dados local)
  ├── imagens/           (fotos anotadas)
  └── temp/              (fotos temporárias da webcam)


📤 SINCRONIZAÇÃO COM SERVIDOR
------------------------------
Após coletar várias imagens:

1. Clique em "Exportar para Sincronização"
2. Será criada uma pasta com:
   - dados_exportacao.json (informações das anotações)
   - produtos.json (lista de produtos)
   - imagens/ (fotos anotadas)

3. Leve esta pasta para a máquina com o servidor Django

4. Execute o script de importação:
   python importar_dados_coletados.py <caminho_da_pasta>

5. Pronto! Os dados estarão no sistema principal


🔧 REQUISITOS
-------------
- Windows 7 ou superior
- 2 GB de RAM
- 500 MB de espaço livre
- Webcam (opcional, apenas para tirar fotos)


⌨️ ATALHOS ÚTEIS
----------------
- ESC: Cancelar captura de webcam
- ESPAÇO: Capturar foto na webcam
- Duplo-clique: Remover anotação selecionada


❓ DÚVIDAS FREQUENTES
---------------------

P: Como remover uma anotação errada?
R: Dê duplo-clique na anotação na lista da direita.

P: Posso anotar o mesmo produto várias vezes na mesma foto?
R: Sim! Cada produto que aparece deve ter seu próprio retângulo.

P: E se eu fechar o programa sem exportar?
R: Tudo bem! Os dados ficam salvos localmente. Você pode exportar
   depois quando quiser.

P: Precisa de internet?
R: Não! O sistema funciona 100% offline.

P: Como atualizar a lista de produtos?
R: Use "Adicionar Novo Produto" ou importe uma lista atualizada
   do servidor principal.


📞 SUPORTE
----------
Em caso de dúvidas ou problemas, contate o gestor responsável.


Versão: 1.0
Data: 26/11/2025
Desenvolvido para: VerifiK - Sistema de IA
