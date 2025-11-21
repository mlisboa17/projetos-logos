"""
╔══════════════════════════════════════════════════════════════════╗
║                    ADMIN - FUEL_PRICES APP                       ║
║           Configuração da Interface Administrativa Django        ║
╚══════════════════════════════════════════════════════════════════╝

📚 O QUE É ESTE ARQUIVO:
------------------------
Configura como os modelos PostoVibra e PrecoVibra aparecem no Django Admin (/admin/)
Acesso via: http://localhost:8000/admin/
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import PostoVibra, PrecoVibra


# ============================================================
# 🏢 ADMIN: POSTO VIBRA
# ============================================================

@admin.register(PostoVibra)
class PostoVibraAdmin(admin.ModelAdmin):
    """
    Administração de Postos do Grupo Lisboa
    """
    list_display = [
        'nome_fantasia',
        'codigo_vibra',
        'cnpj',
        'ativo',
        'created_at'
    ]
    
    list_filter = [
        'ativo',
        'created_at'
    ]
    
    search_fields = [
        'nome_fantasia',
        'razao_social',
        'cnpj',
        'codigo_vibra'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('📝 Dados Básicos', {
            'fields': ('codigo_vibra', 'nome_fantasia', 'razao_social', 'cnpj')
        }),
        ('✅ Status', {
            'fields': ('ativo',)
        }),
        ('🗂️ Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================================
# 💰 ADMIN: PREÇO VIBRA
# ============================================================

@admin.register(PrecoVibra)
class PrecoVibraAdmin(admin.ModelAdmin):
    """
    Administração de Preços Coletados da Vibra
    """
    list_display = [
        'produto_nome',
        'posto',
        'preco_formatado',
        'prazo_pagamento',
        'modalidade',
        'data_coleta',
        'disponivel_badge'
    ]
    
    list_filter = [
        'disponivel',
        'data_coleta',
        'posto',
        'modalidade'
    ]
    
    search_fields = [
        'produto_nome',
        'produto_codigo',
        'posto__nome_fantasia',
        'posto__cnpj'
    ]
    
    readonly_fields = ['created_at']
    
    date_hierarchy = 'data_coleta'
    
    fieldsets = (
        ('🏢 Posto', {
            'fields': ('posto',)
        }),
        ('📦 Produto', {
            'fields': ('produto_nome', 'produto_codigo')
        }),
        ('💰 Preço', {
            'fields': ('preco', 'prazo_pagamento', 'modalidade')
        }),
        ('📍 Distribuição', {
            'fields': ('base_distribuicao',)
        }),
        ('✅ Status', {
            'fields': ('disponivel', 'data_coleta')
        }),
        ('🗂️ Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    # ──────────────────────────────────────────────────────────
    # 🎨 MÉTODOS DE EXIBIÇÃO CUSTOMIZADOS
    # ──────────────────────────────────────────────────────────
    
    @admin.display(description='Preço', ordering='preco')
    def preco_formatado(self, obj):
        """Exibe preço formatado"""
        return format_html(
            '<strong>R$ {:.4f}</strong>',
            obj.preco
        )
    
    @admin.display(description='Status', ordering='disponivel')
    def disponivel_badge(self, obj):
        """Badge de disponibilidade"""
        if obj.disponivel:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 8px; border-radius: 3px;">✅ Disponível</span>'
            )
        return format_html(
            '<span style="background: #dc3545; color: white; padding: 2px 8px; border-radius: 3px;">❌ Indisponível</span>'
        )
    
    # ──────────────────────────────────────────────────────────
    # ⚙️ AÇÕES EM LOTE
    # ──────────────────────────────────────────────────────────
    
    actions = ['marcar_disponivel', 'marcar_indisponivel', 'deletar_antigos']
    
    @admin.action(description='✅ Marcar como disponível')
    def marcar_disponivel(self, request, queryset):
        """Marca preços selecionados como disponíveis"""
        updated = queryset.update(disponivel=True)
        self.message_user(request, f'✅ {updated} preço(s) marcado(s) como disponível!')
    
    @admin.action(description='❌ Marcar como indisponível')
    def marcar_indisponivel(self, request, queryset):
        """Marca preços selecionados como indisponíveis"""
        updated = queryset.update(disponivel=False)
        self.message_user(request, f'❌ {updated} preço(s) marcado(s) como indisponível!')
    
    @admin.action(description='🗑️ Deletar preços > 90 dias')
    def deletar_antigos(self, request, queryset):
        """Remove preços muito antigos"""
        from datetime import timedelta
        from django.utils import timezone
        cutoff = timezone.now() - timedelta(days=90)
        deleted = queryset.filter(data_coleta__lt=cutoff).delete()
        self.message_user(request, f'🗑️ {deleted[0]} preço(s) antigo(s) deletado(s)!')
