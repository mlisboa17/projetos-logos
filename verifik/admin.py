from django.contrib import admin
from .models import (
    Funcionario, PerfilGestor, ProdutoMae, CodigoBarrasProdutoMae, OperacaoVenda, ItemVenda,
    DeteccaoProduto, Incidente, EvidenciaIncidente, Alerta,
    Camera, CameraStatus, ImagemProduto
)
from .models_coleta import ImagemProdutoPendente, LoteFotos
from .models_anotacao import ImagemAnotada, AnotacaoProduto


# ==============================================
# 🧑 FUNCIONÁRIOS E USUÁRIOS
# ==============================================

@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ['matricula', 'nome_completo', 'cargo', 'ativo', 'data_admissao']
    list_filter = ['ativo', 'cargo', 'data_admissao']
    search_fields = ['nome_completo', 'cpf', 'matricula']
    date_hierarchy = 'data_admissao'


@admin.register(PerfilGestor)
class PerfilGestorAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'nivel_acesso', 'telefone', 'receber_alertas_email', 'receber_alertas_whatsapp']
    list_filter = ['nivel_acesso', 'receber_alertas_email', 'receber_alertas_whatsapp']
    search_fields = ['usuario__username', 'usuario__first_name', 'usuario__last_name', 'telefone']


# ==============================================
# 🛒 OPERAÇÕES E PRODUTOS
# ==============================================

class ImagemProdutoInline(admin.TabularInline):
    model = ImagemProduto
    extra = 3
    fields = ['imagem', 'descricao', 'ordem', 'ativa']


class CodigoBarrasInline(admin.TabularInline):
    model = CodigoBarrasProdutoMae
    extra = 2
    fields = ['codigo', 'principal']


@admin.register(ProdutoMae)
class ProdutoMaeAdmin(admin.ModelAdmin):
    list_display = ['descricao_produto', 'marca', 'tipo', 'preco', 'ativo', 'total_imagens', 'total_codigos']
    list_filter = ['ativo', 'tipo', 'marca']
    search_fields = ['descricao_produto', 'marca', 'codigos_barras__codigo']
    inlines = [CodigoBarrasInline, ImagemProdutoInline]
    
    def total_imagens(self, obj):
        return obj.imagens_treino.count()
    total_imagens.short_description = 'Imagens Treino'
    
    def total_codigos(self, obj):
        return obj.codigos_barras.count()
    total_codigos.short_description = 'Códigos'


@admin.register(CodigoBarrasProdutoMae)
class CodigoBarrasProdutoMaeAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'produto_mae', 'principal', 'created_at']
    list_filter = ['principal', 'created_at']
    search_fields = ['codigo', 'produto_mae__descricao_produto']


@admin.register(ImagemProduto)
class ImagemProdutoAdmin(admin.ModelAdmin):
    list_display = ['produto', 'ordem', 'descricao', 'ativa', 'created_at']
    list_filter = ['ativa', 'created_at']
    search_fields = ['produto__descricao_produto', 'descricao']


class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 0


@admin.register(OperacaoVenda)
class OperacaoVendaAdmin(admin.ModelAdmin):
    list_display = ['numero_venda', 'funcionario', 'data_hora', 'valor_total', 'status']
    list_filter = ['status', 'data_hora']
    search_fields = ['numero_venda', 'funcionario__nome_completo']
    date_hierarchy = 'data_hora'
    inlines = [ItemVendaInline]


@admin.register(DeteccaoProduto)
class DeteccaoProdutoAdmin(admin.ModelAdmin):
    list_display = ['produto_identificado', 'camera', 'data_hora_deteccao', 'metodo_deteccao', 'confianca']
    list_filter = ['metodo_deteccao', 'data_hora_deteccao', 'camera']
    search_fields = ['marca_detectada', 'tipo_detectado', 'codigo_detectado']
    date_hierarchy = 'data_hora_deteccao'


# ==============================================
# 🚨 INCIDENTES E EVIDÊNCIAS
# ==============================================

class EvidenciaIncidenteInline(admin.TabularInline):
    model = EvidenciaIncidente
    extra = 0


@admin.register(Incidente)
class IncidenteAdmin(admin.ModelAdmin):
    list_display = ['codigo_incidente', 'tipo', 'status', 'funcionario', 'data_hora_ocorrencia', 'valor_estimado']
    list_filter = ['status', 'tipo', 'data_hora_ocorrencia']
    search_fields = ['codigo_incidente', 'descricao', 'funcionario__nome_completo']
    date_hierarchy = 'data_hora_ocorrencia'
    inlines = [EvidenciaIncidenteInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EvidenciaIncidente)
class EvidenciaIncidenteAdmin(admin.ModelAdmin):
    list_display = ['incidente', 'tipo', 'descricao', 'created_at']
    list_filter = ['tipo', 'created_at']
    search_fields = ['descricao', 'incidente__codigo_incidente']
    date_hierarchy = 'created_at'


# ==============================================
# 📢 ALERTAS
# ==============================================

@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'prioridade', 'canal', 'status', 'destinatario', 'data_criacao']
    list_filter = ['tipo', 'prioridade', 'canal', 'status', 'data_criacao']
    search_fields = ['titulo', 'mensagem', 'destinatario__username']
    date_hierarchy = 'data_criacao'
    readonly_fields = ['data_criacao', 'data_envio', 'data_leitura']


# ==============================================
# 📹 CÂMERAS E MONITORAMENTO
# ==============================================

@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ['nome', 'localizacao', 'ip_address', 'status', 'ativa', 'ultima_conexao']
    list_filter = ['status', 'ativa', 'localizacao']
    search_fields = ['nome', 'localizacao', 'ip_address']
    readonly_fields = ['ultima_conexao', 'ultima_deteccao', 'created_at', 'updated_at']


@admin.register(CameraStatus)
class CameraStatusAdmin(admin.ModelAdmin):
    list_display = ['camera', 'status', 'data_hora', 'qualidade_sinal', 'fps_atual', 'latencia_ms']
    list_filter = ['status', 'data_hora', 'camera']
    search_fields = ['camera__nome', 'mensagem_erro']
    date_hierarchy = 'data_hora'
    readonly_fields = ['data_hora']


# ==============================================
# 📸 COLETA DE IMAGENS
# ==============================================

@admin.register(ImagemProdutoPendente)
class ImagemProdutoPendenteAdmin(admin.ModelAdmin):
    list_display = ['produto', 'status', 'enviado_por', 'data_envio', 'aprovado_por', 'qualidade']
    list_filter = ['status', 'data_envio', 'qualidade', 'produto']
    search_fields = ['produto__nome', 'enviado_por__username', 'aprovado_por__username', 'observacoes']
    date_hierarchy = 'data_envio'
    readonly_fields = ['data_envio']
    
    fieldsets = (
        ('Informações do Produto', {
            'fields': ('produto', 'imagem', 'lote')
        }),
        ('Status e Qualidade', {
            'fields': ('status', 'qualidade', 'observacoes', 'motivo_rejeicao')
        }),
        ('Rastreamento', {
            'fields': ('enviado_por', 'data_envio', 'aprovado_por', 'data_aprovacao')
        }),
    )
    
    actions = ['aprovar_selecionadas', 'rejeitar_selecionadas']
    
    def aprovar_selecionadas(self, request, queryset):
        count = 0
        for imagem in queryset.filter(status='pendente'):
            imagem.status = 'aprovada'
            imagem.aprovado_por = request.user
            imagem.qualidade = 3  # Qualidade padrão
            imagem.save()
            count += 1
        self.message_user(request, f'{count} imagens aprovadas com sucesso!')
    aprovar_selecionadas.short_description = "✓ Aprovar imagens selecionadas"
    
    def rejeitar_selecionadas(self, request, queryset):
        count = 0
        for imagem in queryset.filter(status='pendente'):
            imagem.status = 'rejeitada'
            imagem.aprovado_por = request.user
            imagem.motivo_rejeicao = 'Rejeitada em lote'
            imagem.save()
            count += 1
        self.message_user(request, f'{count} imagens rejeitadas.')
    rejeitar_selecionadas.short_description = "✗ Rejeitar imagens selecionadas"


@admin.register(LoteFotos)
class LoteFotosAdmin(admin.ModelAdmin):
    list_display = ['nome', 'enviado_por', 'data_criacao', 'total_imagens', 'imagens_aprovadas', 'imagens_rejeitadas', 'progresso']
    list_filter = ['data_criacao', 'enviado_por']
    search_fields = ['nome', 'enviado_por__username', 'descricao']
    date_hierarchy = 'data_criacao'
    readonly_fields = ['data_criacao', 'total_imagens', 'imagens_aprovadas', 'imagens_rejeitadas', 'progresso']
    
    def progresso(self, obj):
        if obj.total_imagens == 0:
            return "0%"
        processadas = obj.imagens_aprovadas + obj.imagens_rejeitadas
        percentual = (processadas / obj.total_imagens) * 100
        return f"{percentual:.1f}%"
    progresso.short_description = "Progresso"


# ==============================================
# 📦 ANOTAÇÃO DE IMAGENS
# ==============================================

@admin.register(ImagemAnotada)
class ImagemAnotadaAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'enviado_por', 'data_envio', 'total_anotacoes', 'aprovado_por']
    list_filter = ['status', 'data_envio', 'aprovado_por']
    search_fields = ['enviado_por__username', 'aprovado_por__username', 'observacoes']
    date_hierarchy = 'data_envio'
    readonly_fields = ['data_envio', 'total_anotacoes']
    
    fieldsets = (
        ('Imagem', {
            'fields': ('imagem', 'observacoes')
        }),
        ('Status', {
            'fields': ('status', 'total_anotacoes')
        }),
        ('Rastreamento', {
            'fields': ('enviado_por', 'data_envio', 'aprovado_por', 'data_aprovacao')
        }),
    )


class AnotacaoProdutoInline(admin.TabularInline):
    model = AnotacaoProduto
    extra = 0
    readonly_fields = ['data_criacao']
    fields = ['produto', 'bbox_x', 'bbox_y', 'bbox_width', 'bbox_height', 'confianca', 'observacoes']


@admin.register(AnotacaoProduto)
class AnotacaoProdutoAdmin(admin.ModelAdmin):
    list_display = ['id', 'imagem_anotada', 'produto', 'confianca', 'data_criacao']
    list_filter = ['produto', 'data_criacao']
    search_fields = ['produto__nome', 'observacoes']
    date_hierarchy = 'data_criacao'
    readonly_fields = ['data_criacao', 'get_yolo_format']
    
    fieldsets = (
        ('Vinculação', {
            'fields': ('imagem_anotada', 'produto')
        }),
        ('Bounding Box', {
            'fields': ('bbox_x', 'bbox_y', 'bbox_width', 'bbox_height', 'confianca')
        }),
        ('Informações', {
            'fields': ('observacoes', 'data_criacao', 'get_yolo_format')
        }),
    )
    
    def get_yolo_format(self, obj):
        return obj.get_yolo_format()
    get_yolo_format.short_description = "Formato YOLO"
