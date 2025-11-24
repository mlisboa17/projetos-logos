"""
Script para corrigir links que apontam para admin do Django
Direcionar para views customizadas do VerifiK
"""
import os

PRODUTO_DETALHE = r"c:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\verifik\templates\verifik\produto_detalhe.html"
PRODUTOS_LISTA = r"c:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\verifik\templates\verifik\produtos_lista.html"

def corrigir_produto_detalhe():
    """Corrige produto_detalhe.html"""
    print("=" * 70)
    print("CORRIGINDO produto_detalhe.html")
    print("=" * 70)
    
    with open(PRODUTO_DETALHE, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Backup
    with open(PRODUTO_DETALHE + '.bak2', 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"✅ Backup criado: {PRODUTO_DETALHE}.bak2")
    
    # Correção 1: Botão "Editar Produto" (linha ~66)
    botao_antigo_1 = '<a href="/admin/verifik/produto/{{ produto.pk }}/change/" class="btn" style="margin-right: 1rem;">'
    botao_novo_1 = '<a href="{% url \'verifik_produto_editar\' produto.pk %}" class="btn" style="margin-right: 1rem;">'
    
    if botao_antigo_1 in conteudo:
        conteudo = conteudo.replace(botao_antigo_1, botao_novo_1)
        print("✅ Botão 'Editar Produto' corrigido → usa view customizada")
    else:
        print("⚠️ Botão 'Editar Produto' não encontrado ou já corrigido")
    
    # Correção 2: Botão "Adicionar Imagens" no final (linha ~206)
    botao_antigo_2 = '<a href="/admin/verifik/imagemproduto/add/?produto={{ produto.pk }}" class="btn" style="background: #27ae60;">'
    # Remover esse botão completamente (já existe formulário de upload acima)
    
    if botao_antigo_2 in conteudo:
        # Remover botão e a div que o contém
        conteudo = conteudo.replace(
            '''    <div style="margin-top: 1.5rem;">
        <a href="/admin/verifik/imagemproduto/add/?produto={{ produto.pk }}" class="btn" style="background: #27ae60;">
            ➕ Adicionar Imagens
        </a>
    </div>''',
            ''
        )
        print("✅ Botão duplicado 'Adicionar Imagens' removido (já existe formulário)")
    else:
        print("⚠️ Botão duplicado não encontrado ou já removido")
    
    # Salvar
    with open(PRODUTO_DETALHE, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"✅ Arquivo salvo: {PRODUTO_DETALHE}\n")


def corrigir_produtos_lista():
    """Corrige produtos_lista.html"""
    print("=" * 70)
    print("CORRIGINDO produtos_lista.html")
    print("=" * 70)
    
    with open(PRODUTOS_LISTA, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Backup
    with open(PRODUTOS_LISTA + '.bak2', 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"✅ Backup criado: {PRODUTOS_LISTA}.bak2")
    
    # Correção: Botão grande "Adicionar Novo Produto" no final (linha ~107)
    botao_antigo = '''<div style="text-align: center; margin-top: 2rem;">
    <a href="/admin/verifik/produto/add/" class="btn" style="background: #27ae60;">
        ➕ Adicionar Novo Produto
    </a>
</div>'''
    
    botao_novo = '''<div style="text-align: center; margin-top: 2.5rem; margin-bottom: 1rem;">
    <a href="{% url 'verifik_produto_criar' %}" 
       class="btn" 
       style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
              color: white; 
              font-size: 1.3rem; 
              padding: 1rem 2.5rem; 
              border-radius: 12px; 
              font-weight: bold; 
              box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
              transition: transform 0.2s, box-shadow 0.2s;
              display: inline-block;"
       onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 25px rgba(102, 126, 234, 0.5)'"
       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 6px 20px rgba(102, 126, 234, 0.4)'">
        <i class="bi bi-plus-circle-fill"></i> ➕ Adicionar Novo Produto
    </a>
</div>'''
    
    if botao_antigo in conteudo:
        conteudo = conteudo.replace(botao_antigo, botao_novo)
        print("✅ Botão 'Adicionar Novo Produto' corrigido → usa view customizada")
        print("   + Botão agora com gradiente roxo e efeito hover")
    else:
        print("⚠️ Botão não encontrado ou já corrigido")
    
    # Salvar
    with open(PRODUTOS_LISTA, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"✅ Arquivo salvo: {PRODUTOS_LISTA}\n")


def main():
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║     CORRIGINDO LINKS DO ADMIN → VIEWS CUSTOMIZADAS VERIFIK      ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    
    corrigir_produto_detalhe()
    corrigir_produtos_lista()
    
    print("=" * 70)
    print("RESUMO DAS CORREÇÕES")
    print("=" * 70)
    print("✅ produto_detalhe.html:")
    print("   - Botão 'Editar Produto' → verifik_produto_editar")
    print("   - Botão duplicado 'Adicionar Imagens' → Removido")
    print()
    print("✅ produtos_lista.html:")
    print("   - Botão 'Adicionar Novo Produto' → verifik_produto_criar")
    print("   - Estilo melhorado (gradiente roxo + hover)")
    print()
    print("=" * 70)
    print("AGORA OS BOTÕES USAM AS VIEWS CUSTOMIZADAS DO VERIFIK")
    print("=" * 70)
    print()
    print("📝 Backups criados:")
    print(f"   - {PRODUTO_DETALHE}.bak2")
    print(f"   - {PRODUTOS_LISTA}.bak2")
    print()
    print("🔄 Servidor Django irá recarregar automaticamente")
    print()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
