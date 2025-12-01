from django.contrib import admin
from .models import (
    Funcionario, PerfilGestor, ProdutoMae, CodigoBarrasProdutoMae, OperacaoVenda, ItemVenda,
    DeteccaoProduto, Incidente, EvidenciaIncidente, Alerta,
    Camera, CameraStatus, ImagemProduto,
    Categoria, Marca, Recipiente  # Novas tabelas
)
from .models_coleta import ImagemProdutoPendente, LoteFotos
from .models_anotacao import ImagemAnotada, AnotacaoProduto, ImagemUnificada, HistoricoTreino, ImagemTreino


# ==============================================
# 📁 CATEGORIAS, MARCAS E RECIPIENTES
# ==============================================

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'descricao', 'ativo', 'total_produtos']
    list_filter = ['ativo']
    search_fields = ['nome', 'descricao']
    
    def total_produtos(self, obj):
        return obj.produtos.count()
    total_produtos.short_description = 'Produtos'


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'categoria', 'aliases', 'ativo', 'total_produtos']
    list_filter = ['ativo', 'categoria']
    search_fields = ['nome', 'aliases']
    
    def total_produtos(self, obj):
        return obj.produtos.count()
    total_produtos.short_description = 'Produtos'


@admin.register(Recipiente)
class RecipienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'volume_ml', 'aliases', 'ativo', 'total_produtos']
    list_filter = ['ativo', 'volume_ml']
    search_fields = ['nome', 'aliases']
    
    def total_produtos(self, obj):
        return obj.produtos.count()
    total_produtos.short_description = 'Produtos'


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
    list_display = ['descricao_produto', 'categoria_fk', 'marca_fk', 'recipiente_fk', 'preco', 'ativo', 
                    'treinado', 'qtd_imagens_treino', 'taxa_acerto_display', 'precisa_treino_display']
    list_filter = ['ativo', 'treinado', 'categoria_fk', 'marca_fk', 'recipiente_fk']
    search_fields = ['descricao_produto', 'marca', 'codigos_barras__codigo']
    inlines = [CodigoBarrasInline, ImagemProdutoInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('descricao_produto', 'preco', 'imagem_referencia', 'ativo')
        }),
        ('Classificação (para filtros)', {
            'fields': ('categoria_fk', 'marca_fk', 'recipiente_fk'),
            'description': 'Use esses campos para organizar e filtrar produtos'
        }),
        ('Status de Treinamento IA', {
            'fields': ('treinado', 'data_treinamento', 'qtd_imagens_treino'),
            'description': 'Informações sobre o treinamento da IA para este produto'
        }),
        ('Métricas de Desempenho IA', {
            'fields': ('total_deteccoes', 'total_acertos', 'total_erros'),
            'description': 'Estatísticas de acerto/erro da IA'
        }),
        ('Campos Legado (texto livre)', {
            'fields': ('marca', 'tipo'),
            'classes': ('collapse',),
            'description': 'Campos antigos mantidos para compatibilidade'
        }),
    )
    
    def total_imagens(self, obj):
        return obj.imagens_treino.count()
    total_imagens.short_description = 'Imagens Treino'
    
    def total_codigos(self, obj):
        return obj.codigos_barras.count()
    total_codigos.short_description = 'Códigos'
    
    def taxa_acerto_display(self, obj):
        taxa = obj.taxa_acerto
        if obj.total_deteccoes == 0:
            return "—"
        if taxa >= 90:
            return f"✅ {taxa}%"
        elif taxa >= 70:
            return f"⚠️ {taxa}%"
        else:
            return f"❌ {taxa}%"
    taxa_acerto_display.short_description = 'Taxa Acerto'
    
    def precisa_treino_display(self, obj):
        if obj.precisa_mais_treino:
            return "⚠️ SIM"
        return "✅ OK"
    precisa_treino_display.short_description = 'Precisa Treino?'


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


# ==============================================
#  IMAGENS UNIFICADAS
# ==============================================

@admin.register(ImagemUnificada)
class ImagemUnificadaAdmin(admin.ModelAdmin):
    list_display = ['produto', 'tipo_imagem', 'status', 'num_treinos', 'ativa', 'created_at']
    list_filter = ['tipo_imagem', 'status', 'ativa', 'foi_augmentada']
    search_fields = ['produto__descricao_produto', 'descricao']
    readonly_fields = ['created_at', 'updated_at', 'width', 'height', 'tamanho_bytes']
    
    fieldsets = (
        ('Imagem', {
            'fields': ('produto', 'arquivo', 'tipo_imagem', 'imagem_original')
        }),
        ('Metadados', {
            'fields': ('descricao', 'ordem', 'width', 'height', 'tamanho_bytes')
        }),
        ('Processamento', {
            'fields': ('tipo_processamento', 'foi_augmentada', 'tipo_augmentacao', 'num_augmentacoes')
        }),
        ('Anotacoes', {
            'fields': ('total_anotacoes', 'bbox_x', 'bbox_y', 'bbox_width', 'bbox_height', 'confianca')
        }),
        ('Rastreamento de Treino', {
            'fields': ('num_treinos', 'ultimo_treino', 'versao_modelo')
        }),
        ('Status', {
            'fields': ('status', 'ativa')
        }),
        ('Rastreamento', {
            'fields': ('enviado_por', 'aprovado_por', 'observacoes', 'created_at', 'updated_at', 'data_envio', 'data_aprovacao')
        }),
    )


@admin.register(HistoricoTreino)
class HistoricoTreinoAdmin(admin.ModelAdmin):
    list_display = ['versao_modelo', 'status', 'total_imagens', 'total_produtos', 'acuracia', 'data_inicio']
    list_filter = ['status', 'data_inicio']
    readonly_fields = ['data_inicio', 'data_conclusao']
    
    fieldsets = (
        ('Versao', {
            'fields': ('versao_modelo', 'status')
        }),
        ('Dados de Treino', {
            'fields': ('total_imagens', 'total_produtos', 'epocas')
        }),
        ('Resultados', {
            'fields': ('acuracia', 'perda')
        }),
        ('Rastreamento', {
            'fields': ('data_inicio', 'data_conclusao', 'parametros', 'observacoes')
        }),
    )


@admin.register(ImagemTreino)
class ImagemTreinoAdmin(admin.ModelAdmin):
    list_display = ['imagem', 'historico_treino', 'foi_usada', 'data_adicao']
    list_filter = ['foi_usada', 'historico_treino']
    search_fields = ['imagem__produto__descricao_produto']
    readonly_fields = ['data_adicao']
