from django.contrib import admin
from .models import (
    Funcionario, PerfilGestor, Produto, OperacaoVenda, ItemVenda,
    DeteccaoProduto, Incidente, EvidenciaIncidente, Alerta,
    Camera, CameraStatus, ImagemProduto
)


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


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['codigo_barras', 'descricao_produto', 'marca', 'tipo', 'preco', 'ativo', 'total_imagens']
    list_filter = ['ativo', 'tipo', 'marca']
    search_fields = ['descricao_produto', 'codigo_barras', 'marca']
    inlines = [ImagemProdutoInline]
    
    def total_imagens(self, obj):
        return obj.imagens_treino.count()
    total_imagens.short_description = 'Imagens Treino'


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
