from django.contrib import admin
from .models import Empresa, TipoDocumento, FechamentoCaixa, DocumentoTranscrito, ItemDocumento


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cnpj', 'ativo', 'criado_em']
    list_filter = ['ativo', 'criado_em']
    search_fields = ['nome', 'cnpj']
    date_hierarchy = 'criado_em'


@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome', 'descricao']


class DocumentoTranscritoInline(admin.TabularInline):
    model = DocumentoTranscrito
    extra = 0
    fields = ['tipo_documento', 'tipo_movimento', 'valor_total', 'status', 'confianca_ocr']
    readonly_fields = ['status', 'confianca_ocr']
    can_delete = False


@admin.register(FechamentoCaixa)
class FechamentoCaixaAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'data_fechamento', 'status', 'total_vendas', 'total_despesas', 'total_liquido', 'total_documentos', 'criado_em']
    list_filter = ['status', 'empresa', 'data_fechamento']
    search_fields = ['empresa__nome', 'observacoes']
    date_hierarchy = 'data_fechamento'
    readonly_fields = ['total_vendas', 'total_despesas', 'total_liquido', 'total_documentos', 'documentos_processados', 'documentos_revisados', 'criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'data_fechamento', 'status')
        }),
        ('Totalizadores', {
            'fields': ('total_vendas', 'total_despesas', 'total_liquido', 'total_documentos', 'documentos_processados', 'documentos_revisados')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Auditoria', {
            'fields': ('criado_por', 'revisado_por', 'criado_em', 'atualizado_em', 'concluido_em'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [DocumentoTranscritoInline]
    
    actions = ['recalcular_totais', 'marcar_como_concluido']
    
    def recalcular_totais(self, request, queryset):
        for fechamento in queryset:
            fechamento.calcular_totais()
        self.message_user(request, f"{queryset.count()} fechamento(s) recalculado(s)")
    recalcular_totais.short_description = "Recalcular totais dos fechamentos selecionados"
    
    def marcar_como_concluido(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(status='concluido', concluido_em=timezone.now())
        self.message_user(request, f"{count} fechamento(s) marcado(s) como concluído")
    marcar_como_concluido.short_description = "Marcar como concluído"


class ItemDocumentoInline(admin.TabularInline):
    model = ItemDocumento
    extra = 1
    fields = ['ordem', 'descricao', 'quantidade', 'valor_unitario', 'valor_total', 'codigo', 'unidade']
    readonly_fields = ['valor_total']


@admin.register(DocumentoTranscrito)
class DocumentoTranscritoAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'fechamento', 'tipo_documento', 'tipo_movimento', 'numero_documento', 'data_documento', 'valor_total', 'status', 'confianca_ocr', 'criado_em']
    list_filter = ['status', 'tipo_movimento', 'tipo_documento', 'fechamento__empresa', 'data_documento']
    search_fields = ['numero_documento', 'texto_completo', 'observacoes']
    date_hierarchy = 'criado_em'
    readonly_fields = ['texto_completo', 'confianca_ocr', 'processado_em', 'revisado_em', 'criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Fechamento', {
            'fields': ('fechamento', 'tipo_documento', 'tipo_movimento')
        }),
        ('Imagens', {
            'fields': ('imagem', 'imagem_processada')
        }),
        ('Dados Transcritos', {
            'fields': ('texto_completo', 'numero_documento', 'data_documento', 'valor_total', 'dados_extraidos')
        }),
        ('Status', {
            'fields': ('status', 'confianca_ocr', 'processado_em')
        }),
        ('Revisão', {
            'fields': ('observacoes', 'correcoes_manuais', 'revisado_por', 'revisado_em')
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ItemDocumentoInline]
    
    actions = ['processar_documentos', 'marcar_como_revisado']
    
    def processar_documentos(self, request, queryset):
        # Aqui você pode chamar a função de OCR em lote
        count = 0
        for doc in queryset:
            if doc.status == 'pendente':
                # TODO: Implementar processamento OCR
                doc.status = 'processado'
                doc.save()
                count += 1
        self.message_user(request, f"{count} documento(s) processado(s)")
    processar_documentos.short_description = "Processar documentos selecionados (OCR)"
    
    def marcar_como_revisado(self, request, queryset):
        count = 0
        for doc in queryset:
            doc.marcar_como_revisado(request.user)
            count += 1
        self.message_user(request, f"{count} documento(s) marcado(s) como revisado")
    marcar_como_revisado.short_description = "Marcar como revisado"


@admin.register(ItemDocumento)
class ItemDocumentoAdmin(admin.ModelAdmin):
    list_display = ['documento', 'descricao', 'quantidade', 'valor_unitario', 'valor_total', 'ordem']
    list_filter = ['documento__fechamento__empresa']
    search_fields = ['descricao', 'codigo']
    readonly_fields = ['valor_total']
