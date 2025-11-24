"""
Script para corrigir filtros do VerifiK - produtos_lista
PROBLEMA: Campo codigo_barras não existe mais em ProdutoMae
SOLUÇÃO: Usar codigos_barras__codigo (relacionamento)
"""

print("""
═══════════════════════════════════════════════════════════════════
CORREÇÕES NECESSÁRIAS NO VERIFIK
═══════════════════════════════════════════════════════════════════

📁 ARQUIVO: verifik/views.py
📍 FUNÇÃO: produtos_lista (linha ~98-130)

❌ PROBLEMA ATUAL:
------------------
if busca:
    produtos = produtos.filter(
        Q(descricao_produto__icontains=busca) |
        Q(marca__icontains=busca) |
        Q(codigo_barras__icontains=busca)  ← ERRO! Campo não existe
    )

✅ CORREÇÃO:
------------
if busca:
    produtos = produtos.filter(
        Q(descricao_produto__icontains=busca) |
        Q(marca__icontains=busca) |
        Q(codigos_barras__codigo__icontains=busca)  ← CORRETO!
    ).distinct()  ← IMPORTANTE: evita duplicatas


═══════════════════════════════════════════════════════════════════
📁 ARQUIVO: verifik/templates/verifik/produtos_lista.html
📍 BOTÃO: "Novo Produto" (linha ~10)

✅ MELHORIAS VISUAIS:
---------------------

ANTES:
<a href="{% url 'verifik_produto_criar' %}" class="btn btn-primary">
    <i class="bi bi-plus-circle"></i> Novo Produto
</a>

DEPOIS:
<a href="{% url 'verifik_produto_criar' %}" 
   class="btn btn-primary" 
   style="font-size: 1.1rem; padding: 0.75rem 1.5rem; font-weight: bold; box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);">
    <i class="bi bi-plus-circle"></i> ➕ Novo Produto
</a>

ADICIONAR NO FINAL (linha ~105):
<div style="text-align: center; margin-top: 2rem;">
    <a href="{% url 'verifik_produto_criar' %}" 
       class="btn" 
       style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
              color: white; 
              font-size: 1.2rem; 
              padding: 1rem 2rem; 
              border-radius: 10px; 
              font-weight: bold; 
              box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
              transition: transform 0.2s;"
       onmouseover="this.style.transform='scale(1.05)'"
       onmouseout="this.style.transform='scale(1)'">
        ➕ Adicionar Novo Produto
    </a>
</div>


═══════════════════════════════════════════════════════════════════
📝 CÓDIGO COMPLETO CORRIGIDO - verifik/views.py
═══════════════════════════════════════════════════════════════════

@login_required(login_url='login')
def produtos_lista(request):
    \"\"\"Lista de produtos com imagens e filtros\"\"\"
    produtos = ProdutoMae.objects.prefetch_related('imagens_treino', 'codigos_barras').filter(ativo=True)
    
    # Filtros
    tipo_filtro = request.GET.get('tipo')
    busca = request.GET.get('q')
    imagens_filtro = request.GET.get('imagens')
    
    if tipo_filtro:
        produtos = produtos.filter(tipo__icontains=tipo_filtro)
    
    if busca:
        produtos = produtos.filter(
            Q(descricao_produto__icontains=busca) |
            Q(marca__icontains=busca) |
            Q(codigos_barras__codigo__icontains=busca)  # CORRIGIDO!
        ).distinct()  # IMPORTANTE: Remove duplicatas
    
    # Filtro por imagens
    if imagens_filtro == 'com':
        produtos = produtos.exclude(imagens_treino__isnull=True).distinct()
    elif imagens_filtro == 'sem':
        produtos = produtos.filter(imagens_treino__isnull=True)
    
    permissions = get_user_permissions(request.user)
    
    context = {
        'produtos': produtos,
        'tipo_filtro': tipo_filtro,
        'busca': busca,
        'imagens_filtro': imagens_filtro,
        **permissions,
    }
    
    return render(request, 'verifik/produtos_lista.html', context)


═══════════════════════════════════════════════════════════════════
🎯 INSTRUÇÕES:
═══════════════════════════════════════════════════════════════════

1. Editar verifik/views.py (linha ~98-130)
   - Mudar Q(codigo_barras__icontains=busca) 
   - Para Q(codigos_barras__codigo__icontains=busca)
   - Adicionar .distinct() após o filter

2. Editar verifik/templates/verifik/produtos_lista.html
   - Melhorar botão "Novo Produto" no topo
   - Adicionar botão grande no final da lista

3. Testar filtros:
   - Buscar por nome: "Coca"
   - Buscar por marca: "Coca-Cola"
   - Buscar por código: "789490"
   - Filtrar por tipo
   - Filtrar por imagens

═══════════════════════════════════════════════════════════════════
""")
