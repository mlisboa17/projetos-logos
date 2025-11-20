"""
Admin para models estendidos
"""
from django.contrib import admin
from .models_extended import (
    Empresa, PostoCombustivel, Restaurante, SistemaEnergiaSolar,
    LojaConveniencia, CentroLubrificacao
)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = [
        'nome_fantasia',
        'razao_social',
        'cnpj',
        'cidade',
        'estado',
        'regime_tributario',
        'ativa'
    ]
    list_filter = ['ativa', 'estado', 'regime_tributario', 'organization']
    search_fields = ['razao_social', 'nome_fantasia', 'cnpj']
    
    fieldsets = (
        ('Organização', {
            'fields': ('organization',)
        }),
        ('Identificação', {
            'fields': (
                'razao_social',
                'nome_fantasia',
                'cnpj',
                'inscricao_municipal',
                'inscricao_estadual'
            )
        }),
        ('Endereço', {
            'fields': (
                'cep',
                'tipo_logradouro',
                'logradouro',
                'numero',
                'complemento',
                'bairro',
                'cidade',
                'estado'
            )
        }),
        ('Contato', {
            'fields': (
                'telefone',
                'celular',
                'fax',
                'email_contato'
            )
        }),
        ('Gestão', {
            'fields': (
                'proprietario',
                'gerente',
                'nome_declarante',
                'cpf_declarante'
            )
        }),
        ('Tributação', {
            'fields': ('regime_tributario',)
        }),
        ('Códigos e Identificadores', {
            'fields': (
                'codigo_receita',
                'codigo_externo',
                'logomarca'
            ),
            'classes': ('collapse',)
        }),
        ('Controle', {
            'fields': (
                'ativa',
                'data_abertura',
                'observacoes'
            )
        }),
    )


@admin.register(PostoCombustivel)
class PostoCombustivelAdmin(admin.ModelAdmin):
    list_display = [
        'nome_fantasia',
        'bandeira',
        'cidade',
        'numero_bombas',
        'tem_conveniencia',
        'ativa'
    ]
    list_filter = ['bandeira', 'tem_conveniencia', 'ativa', 'estado', 'organization']
    search_fields = ['razao_social', 'nome_fantasia', 'cnpj', 'codigo_anp']
    
    fieldsets = (
        ('Organização', {
            'fields': ('organization',)
        }),
        ('Identificação', {
            'fields': (
                'razao_social',
                'nome_fantasia',
                'cnpj',
                'inscricao_municipal',
                'inscricao_estadual',
                'bandeira',
                'codigo_anp'
            )
        }),
        ('Endereço', {
            'fields': (
                'cep',
                'tipo_logradouro',
                'logradouro',
                'numero',
                'complemento',
                'bairro',
                'cidade',
                'estado'
            )
        }),
        ('Serviços e Estrutura', {
            'fields': (
                'servicos',
                'tem_conveniencia',
                'numero_bombas',
                'numero_tanques',
                'numero_pistas'
            )
        }),
        ('Capacidade dos Tanques', {
            'fields': (
                'capacidade_gasolina_comum',
                'capacidade_gasolina_aditivada',
                'capacidade_diesel_s10',
                'capacidade_diesel_comum',
                'capacidade_etanol'
            ),
            'classes': ('collapse',)
        }),
        ('Horário de Funcionamento', {
            'fields': (
                'funciona_24h',
                'horario_abertura',
                'horario_fechamento'
            )
        }),
        ('Integrações', {
            'fields': (
                'usa_webpostos',
                'codigo_webpostos'
            )
        }),
        ('Contato', {
            'fields': (
                'telefone',
                'celular',
                'email_contato'
            ),
            'classes': ('collapse',)
        }),
        ('Gestão', {
            'fields': (
                'proprietario',
                'gerente'
            ),
            'classes': ('collapse',)
        }),
        ('Controle', {
            'fields': (
                'ativa',
                'data_abertura',
                'observacoes'
            ),
            'classes': ('collapse',)
        }),
    )


@admin.register(Restaurante)
class RestauranteAdmin(admin.ModelAdmin):
    list_display = [
        'nome_fantasia',
        'tipo',
        'e_franquia',
        'nome_franquia',
        'cidade',
        'aceita_delivery',
        'ativa'
    ]
    list_filter = ['tipo', 'e_franquia', 'aceita_delivery', 'tem_ifood', 'ativa', 'organization']
    search_fields = ['razao_social', 'nome_fantasia', 'cnpj', 'nome_franquia']
    
    fieldsets = (
        ('Organização', {
            'fields': ('organization',)
        }),
        ('Identificação', {
            'fields': (
                'razao_social',
                'nome_fantasia',
                'cnpj',
                'tipo'
            )
        }),
        ('Franquia', {
            'fields': (
                'e_franquia',
                'nome_franquia',
                'codigo_franquia'
            )
        }),
        ('Endereço', {
            'fields': (
                'cep',
                'tipo_logradouro',
                'logradouro',
                'numero',
                'complemento',
                'bairro',
                'cidade',
                'estado'
            ),
            'classes': ('collapse',)
        }),
        ('Capacidade', {
            'fields': (
                'numero_mesas',
                'capacidade_pessoas'
            )
        }),
        ('Delivery', {
            'fields': (
                'aceita_delivery',
                'tem_ifood',
                'tem_uber_eats',
                'tem_rappi'
            )
        }),
        ('Horário', {
            'fields': (
                'horario_abertura',
                'horario_fechamento'
            )
        }),
        ('Contato', {
            'fields': (
                'telefone',
                'celular',
                'email_contato'
            ),
            'classes': ('collapse',)
        }),
        ('Controle', {
            'fields': (
                'ativa',
                'observacoes'
            ),
            'classes': ('collapse',)
        }),
    )


@admin.register(SistemaEnergiaSolar)
class SistemaEnergiaSolarAdmin(admin.ModelAdmin):
    list_display = [
        'nome_fantasia',
        'potencia_instalada_kwp',
        'numero_paineis',
        'geracao_media_mensal_kwh',
        'tem_sistema_monitoramento',
        'ativa'
    ]
    list_filter = ['tem_sistema_monitoramento', 'ativa', 'organization']
    search_fields = ['razao_social', 'nome_fantasia', 'cnpj']
    
    fieldsets = (
        ('Organização', {
            'fields': ('organization',)
        }),
        ('Identificação', {
            'fields': (
                'razao_social',
                'nome_fantasia',
                'cnpj'
            )
        }),
        ('Localização', {
            'fields': (
                'cep',
                'logradouro',
                'numero',
                'bairro',
                'cidade',
                'estado'
            ),
            'classes': ('collapse',)
        }),
        ('Especificações Técnicas', {
            'fields': (
                'potencia_instalada_kwp',
                'numero_paineis',
                'marca_paineis',
                'marca_inversor'
            )
        }),
        ('Geração e Economia', {
            'fields': (
                'geracao_media_mensal_kwh',
                'economia_media_mensal'
            )
        }),
        ('Datas', {
            'fields': (
                'data_instalacao',
                'data_ativacao'
            )
        }),
        ('Monitoramento', {
            'fields': (
                'tem_sistema_monitoramento',
                'url_monitoramento',
                'api_monitoramento'
            )
        }),
        ('Controle', {
            'fields': (
                'ativa',
                'observacoes'
            ),
            'classes': ('collapse',)
        }),
    )


@admin.register(LojaConveniencia)
class LojaConvenienciaAdmin(admin.ModelAdmin):
    list_display = [
        'nome_fantasia',
        'posto',
        'area_m2',
        'numero_checkouts',
        'funciona_24h',
        'ativa'
    ]
    list_filter = ['tem_padaria', 'tem_cafe', 'funciona_24h', 'ativa', 'organization']
    search_fields = ['razao_social', 'nome_fantasia', 'cnpj']
    
    fieldsets = (
        ('Organização', {
            'fields': ('organization',)
        }),
        ('Identificação', {
            'fields': (
                'razao_social',
                'nome_fantasia',
                'cnpj',
                'posto'
            )
        }),
        ('Estrutura', {
            'fields': (
                'area_m2',
                'numero_checkouts',
                'tem_padaria',
                'tem_cafe',
                'tem_freezer'
            )
        }),
        ('Serviços', {
            'fields': (
                'aceita_vale_refeicao',
                'aceita_cartao_combustivel'
            )
        }),
        ('Categorias de Produtos', {
            'fields': (
                'vende_bebidas',
                'vende_alimentos',
                'vende_higiene',
                'vende_automotivos'
            )
        }),
        ('Horário', {
            'fields': (
                'funciona_24h',
                'horario_abertura',
                'horario_fechamento'
            )
        }),
        ('Sistema PDV', {
            'fields': (
                'usa_sistema_pdv',
                'nome_sistema_pdv'
            )
        }),
        ('Endereço', {
            'fields': (
                'cep',
                'logradouro',
                'numero',
                'bairro',
                'cidade',
                'estado'
            ),
            'classes': ('collapse',)
        }),
        ('Controle', {
            'fields': (
                'ativa',
                'observacoes'
            ),
            'classes': ('collapse',)
        }),
    )


@admin.register(CentroLubrificacao)
class CentroLubrificacaoAdmin(admin.ModelAdmin):
    list_display = [
        'nome_fantasia',
        'posto',
        'numero_boxes',
        'atendimentos_dia',
        'ativa'
    ]
    list_filter = [
        'tem_elevador',
        'atende_passeio',
        'atende_caminhao',
        'ativa',
        'organization'
    ]
    search_fields = ['razao_social', 'nome_fantasia', 'cnpj']
    
    fieldsets = (
        ('Organização', {
            'fields': ('organization',)
        }),
        ('Identificação', {
            'fields': (
                'razao_social',
                'nome_fantasia',
                'cnpj',
                'posto'
            )
        }),
        ('Estrutura', {
            'fields': (
                'numero_boxes',
                'tem_elevador',
                'tem_rampa'
            )
        }),
        ('Serviços Oferecidos', {
            'fields': (
                'faz_troca_oleo',
                'faz_troca_filtros',
                'faz_alinhamento',
                'faz_balanceamento',
                'faz_lavagem_motor'
            )
        }),
        ('Tipos de Veículos', {
            'fields': (
                'atende_passeio',
                'atende_moto',
                'atende_caminhao',
                'atende_onibus'
            )
        }),
        ('Produtos', {
            'fields': ('marcas_lubrificantes',)
        }),
        ('Capacidade', {
            'fields': (
                'atendimentos_dia',
                'tempo_medio_atendimento'
            )
        }),
        ('Horário', {
            'fields': (
                'horario_abertura',
                'horario_fechamento'
            )
        }),
        ('Endereço', {
            'fields': (
                'cep',
                'logradouro',
                'numero',
                'bairro',
                'cidade',
                'estado'
            ),
            'classes': ('collapse',)
        }),
        ('Controle', {
            'fields': (
                'ativa',
                'observacoes'
            ),
            'classes': ('collapse',)
        }),
    )
