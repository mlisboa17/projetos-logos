"""
Script para corrigir links do admin Django nos templates do VerifiK
Redireciona para as views customizadas do VerifiK
"""
import os

PRODUTO_DETALHE = r"c:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\verifik\templates\verifik\produto_detalhe.html"
PRODUTOS_LISTA = r"c:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\verifik\templates\verifik\produtos_lista.html"

def corrigir_produto_detalhe():
    """Corrige links no template produto_detalhe.html"""
    print("=" * 70)
    print("CORRIGINDO produto_detalhe.html")
    print("=" * 70)
    
    with open(PRODUTO_DETALHE, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Backup
    with open(PRODUTO_DETALHE + '.bak2', 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"✅ Backup criado")
    
    # Correção 1: Botão "Editar Produto"
    antigo1 = '<a href="/admin/verifik/produto/{{ produto.pk }}/change/" class="btn btn-primary"'
    novo1 = '<a href="{% url \'verifik_produto_editar\' produto.pk %}" class="btn btn-primary"'
    
    if antigo1 in conteudo:
        conteudo = conteudo.replace(antigo1, novo1)
        print("✅ Botão 'Editar Produto' corrigido")
    else:
        print("⚠️ Botão 'Editar Produto' não encontrado ou já corrigido")
    
    # Correção 2: Botão "Adicionar Imagens"
    antigo2 = '<a href="/admin/verifik/imagemproduto/add/?produto={{ produto.pk }}"'
    novo2 = '<a href="{% url \'verifik_adicionar_imagem\' produto.pk %}"'
    
    if antigo2 in conteudo:
        conteudo = conteudo.replace(antigo2, novo2)
        print("✅ Botão 'Adicionar Imagens' corrigido")
    else:
        print("⚠️ Botão 'Adicionar Imagens' não encontrado ou já corrigido")
    
    # Salvar
    with open(PRODUTO_DETALHE, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"✅ Arquivo salvo\n")

def corrigir_produtos_lista():
    """Corrige links no template produtos_lista.html"""
    print("=" * 70)
    print("CORRIGINDO produtos_lista.html")
    print("=" * 70)
    
    with open(PRODUTOS_LISTA, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Backup
    with open(PRODUTOS_LISTA + '.bak2', 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"✅ Backup criado")
    
    # Correção: Botão "Adicionar Novo Produto"
    antigo = '<a href="/admin/verifik/produto/add/" class="btn"'
    novo = '<a href="{% url \'verifik_produto_criar\' %}" class="btn"'
    
    if antigo in conteudo:
        conteudo = conteudo.replace(antigo, novo)
        print("✅ Botão 'Adicionar Novo Produto' corrigido")
    else:
        print("⚠️ Botão 'Adicionar Novo Produto' não encontrado ou já corrigido")
    
    # Salvar
    with open(PRODUTOS_LISTA, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"✅ Arquivo salvo\n")

def main():
    print("\n╔══════════════════════════════════════════════════════════════════╗")
    print("║          CORRIGINDO LINKS DO ADMIN NOS TEMPLATES               ║")
    print("╚══════════════════════════════════════════════════════════════════╝\n")
    
    corrigir_produto_detalhe()
    corrigir_produtos_lista()
    
    print("=" * 70)
    print("RESUMO")
    print("=" * 70)
    print("✅ Templates corrigidos:")
    print("   - produto_detalhe.html: Editar + Adicionar Imagens")
    print("   - produtos_lista.html: Adicionar Novo Produto")
    print()
    print("🔄 Servidor Django recarregará automaticamente")
    print("🌐 Teste em: http://127.0.0.1:8000/verifik/produtos/")
    print("=" * 70)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
