from django.contrib import admin
from .models import ProcessadorImagens

@admin.register(ProcessadorImagens)
class ProcessadorImagensAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'status', 'data_criacao', 'imagem_processada']
    list_filter = ['tipo', 'status', 'data_criacao']
    search_fields = ['imagem_original', 'imagem_processada']
    readonly_fields = ['data_criacao', 'imagem_original', 'imagem_processada', 'tipo']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('tipo', 'status', 'data_criacao')
        }),
        ('Caminhos', {
            'fields': ('imagem_original', 'imagem_processada')
        }),
        ('Detalhes', {
            'fields': ('parametros', 'mensagem_erro'),
            'classes': ('collapse',)
        }),
    )
