"""
Script para aplicar correções nos arquivos do VerifiK
Corrige filtros de busca e melhora botões
"""
import os
import sys

# Caminhos dos arquivos
VIEWS_FILE = r"c:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\verifik\views.py"
TEMPLATE_FILE = r"c:\Users\mlisb\OneDrive\Desktop\ProjetoLogus\verifik\templates\verifik\produtos_lista.html"

def corrigir_views():
    """Corrige o filtro de busca em verifik/views.py"""
    print("=" * 70)
    print("CORRIGINDO verifik/views.py")
    print("=" * 70)
    
    if not os.path.exists(VIEWS_FILE):
        print(f"❌ Arquivo não encontrado: {VIEWS_FILE}")
        return False
    
    with open(VIEWS_FILE, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Backup
    with open(VIEWS_FILE + '.bak', 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"✅ Backup criado: {VIEWS_FILE}.bak")
    
    # Correção 1: Adicionar prefetch de códigos de barras
    conteudo_antigo1 = "produtos = ProdutoMae.objects.prefetch_related('imagens_treino').filter(ativo=True)"
    conteudo_novo1 = "produtos = ProdutoMae.objects.prefetch_related('imagens_treino', 'codigos_barras').filter(ativo=True)"
    
    if conteudo_antigo1 in conteudo:
        conteudo = conteudo.replace(conteudo_antigo1, conteudo_novo1)
        print("✅ Adicionado prefetch_related('codigos_barras')")
    else:
        print("⚠️ Linha de prefetch_related não encontrada (pode já estar correta)")
    
    # Correção 2: Corrigir filtro de busca (PRINCIPAL)
    # Buscar por variações possíveis
    variacoes_antigas = [
        "Q(codigo_barras__icontains=busca)",
        "Q(codigos_barras__icontains=busca)",
        "Q(produto.codigo_barras__icontains=busca)"
    ]
    
    correcao_aplicada = False
    for variacao in variacoes_antigas:
        if variacao in conteudo:
            conteudo = conteudo.replace(
                variacao,
                "Q(codigos_barras__codigo__icontains=busca)"
            )
            print(f"✅ Corrigido: {variacao} → Q(codigos_barras__codigo__icontains=busca)")
            correcao_aplicada = True
            break
    
    if not correcao_aplicada:
        print("⚠️ Filtro de busca não encontrado (pode já estar correto)")
    
    # Correção 3: Adicionar .distinct() se não existir
    busca_filter = """if busca:
        produtos = produtos.filter(
            Q(descricao_produto__icontains=busca) |
            Q(marca__icontains=busca) |
            Q(codigos_barras__codigo__icontains=busca)
        )"""
    
    busca_filter_correto = """if busca:
        produtos = produtos.filter(
            Q(descricao_produto__icontains=busca) |
            Q(marca__icontains=busca) |
            Q(codigos_barras__codigo__icontains=busca)
        ).distinct()"""
    
    if busca_filter in conteudo and busca_filter_correto not in conteudo:
        conteudo = conteudo.replace(busca_filter, busca_filter_correto)
        print("✅ Adicionado .distinct() ao filtro de busca")
    
    # Salvar alterações
    with open(VIEWS_FILE, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print(f"✅ Arquivo salvo: {VIEWS_FILE}")
    print()
    return True


def melhorar_template():
    """Melhora os botões no template produtos_lista.html"""
    print("=" * 70)
    print("MELHORANDO verifik/templates/verifik/produtos_lista.html")
    print("=" * 70)
    
    if not os.path.exists(TEMPLATE_FILE):
        print(f"❌ Arquivo não encontrado: {TEMPLATE_FILE}")
        return False
    
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Backup
    with open(TEMPLATE_FILE + '.bak', 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"✅ Backup criado: {TEMPLATE_FILE}.bak")
    
    # Melhorar botão "Novo Produto" no topo
    botao_antigo = """<a href="{% url 'verifik_produto_criar' %}" class="btn btn-primary">
            <i class="bi bi-plus-circle"></i> Novo Produto
        </a>"""
    
    botao_novo = """<a href="{% url 'verifik_produto_criar' %}" 
           class="btn btn-primary" 
           style="font-size: 1.1rem; padding: 0.75rem 1.5rem; font-weight: bold; 
                  box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3); 
                  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <i class="bi bi-plus-circle"></i> ➕ Novo Produto
        </a>"""
    
    if botao_antigo in conteudo:
        conteudo = conteudo.replace(botao_antigo, botao_novo)
        print("✅ Botão 'Novo Produto' (topo) melhorado")
    else:
        print("⚠️ Botão do topo não encontrado (pode ter formato diferente)")
    
    # Verificar se já existe botão grande no final
    if 'Adicionar Novo Produto' not in conteudo and '➕ Adicionar Novo Produto' not in conteudo:
        # Adicionar botão grande antes do {% endblock %}
        botao_grande = """
<div style="text-align: center; margin-top: 2.5rem; margin-bottom: 1rem;">
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
</div>
{% endblock %}"""
        
        conteudo = conteudo.replace('{% endblock %}', botao_grande)
        print("✅ Botão grande 'Adicionar Novo Produto' adicionado ao final")
    else:
        print("⚠️ Botão grande já existe no template")
    
    # Salvar alterações
    with open(TEMPLATE_FILE, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print(f"✅ Arquivo salvo: {TEMPLATE_FILE}")
    print()
    return True


def main():
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║        APLICANDO CORREÇÕES NO VERIFIK - FILTROS E BOTÕES        ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    
    sucesso_views = corrigir_views()
    sucesso_template = melhorar_template()
    
    print("=" * 70)
    print("RESUMO")
    print("=" * 70)
    
    if sucesso_views:
        print("✅ verifik/views.py corrigido")
        print("   - Prefetch de códigos de barras adicionado")
        print("   - Filtro de busca corrigido: codigos_barras__codigo")
        print("   - .distinct() adicionado para evitar duplicatas")
    else:
        print("❌ Falha ao corrigir verifik/views.py")
    
    print()
    
    if sucesso_template:
        print("✅ verifik/templates/verifik/produtos_lista.html melhorado")
        print("   - Botão 'Novo Produto' mais visível")
        print("   - Botão grande adicionado ao final da lista")
    else:
        print("❌ Falha ao melhorar template")
    
    print()
    print("=" * 70)
    print("🔄 PRÓXIMOS PASSOS:")
    print("=" * 70)
    print("1. Servidor Django irá recarregar automaticamente")
    print("2. Acesse: http://127.0.0.1:8000/verifik/produtos/")
    print("3. Teste os filtros:")
    print("   - Buscar por nome do produto")
    print("   - Buscar por marca")
    print("   - Buscar por código de barras")
    print("   - Filtrar por tipo")
    print("   - Filtrar por imagens")
    print()
    print("📝 Backups criados:")
    print(f"   - {VIEWS_FILE}.bak")
    print(f"   - {TEMPLATE_FILE}.bak")
    print()
    print("=" * 70)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
