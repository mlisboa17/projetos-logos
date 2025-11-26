from django.contrib import admin
from django.utils.html import format_html
from .models_meteorologia import DadosMeteorologicos, AnalisePerformance


@admin.register(DadosMeteorologicos)
class DadosMeteorologicosAdmin(admin.ModelAdmin):
    list_display = ['usina', 'timestamp', 'condicao_clima_badge', 'irradiancia_global_w_m2', 
                    'temperatura_ar_c', 'nebulosidade_percent', 'precipitacao_mm', 'fonte_dados']
    list_filter = ['usina', 'condicao_clima', 'fonte_dados', 'timestamp']
    search_fields = ['usina__nome']
    date_hierarchy = 'timestamp'
    readonly_fields = ['hsp_dia_kwh_m2_display', 'indice_claridade_display']
    
    fieldsets = (
        ('Usina e Timestamp', {
            'fields': ('usina', 'timestamp', 'fonte_dados')
        }),
        ('Irradiação Solar', {
            'fields': ('irradiancia_global_w_m2', 'irradiancia_direta_w_m2', 
                      'irradiancia_difusa_w_m2', 'hsp_dia_kwh_m2_display', 'indice_claridade_display')
        }),
        ('Condições Climáticas', {
            'fields': ('condicao_clima', 'nebulosidade_percent', 'temperatura_ar_c', 'sensacao_termica_c')
        }),
        ('Precipitação', {
            'fields': ('precipitacao_mm', 'chovendo')
        }),
        ('Vento', {
            'fields': ('velocidade_vento_km_h', 'direcao_vento_graus'),
            'classes': ('collapse',)
        }),
        ('Umidade e Pressão', {
            'fields': ('umidade_relativa_percent', 'pressao_atmosferica_hpa', 'ponto_orvalho_c'),
            'classes': ('collapse',)
        }),
    )
    
    def condicao_clima_badge(self, obj):
        cores = {
            'ceu_limpo': '#4CAF50',
            'parcialmente_nublado': '#2196F3',
            'nublado': '#9E9E9E',
            'chuvoso': '#FF9800',
            'tempestade': '#F44336',
            'nevoa': '#607D8B'
        }
        icones = {
            'ceu_limpo': '☀️',
            'parcialmente_nublado': '⛅',
            'nublado': '☁️',
            'chuvoso': '🌧️',
            'tempestade': '⚡',
            'nevoa': '🌫️'
        }
        cor = cores.get(obj.condicao_clima, '#000')
        icone = icones.get(obj.condicao_clima, '')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{} {}</span>',
            cor, icone, obj.get_condicao_clima_display()
        )
    condicao_clima_badge.short_description = 'Condição Climática'
    
    def hsp_dia_kwh_m2_display(self, obj):
        if obj.hsp_dia_kwh_m2:
            return f'{obj.hsp_dia_kwh_m2:.2f} kWh/m²/dia'
        return '-'
    hsp_dia_kwh_m2_display.short_description = 'HSP Diário'
    
    def indice_claridade_display(self, obj):
        if obj.indice_claridade:
            return f'{obj.indice_claridade:.2f}'
        return '-'
    indice_claridade_display.short_description = 'Índice de Claridade'


@admin.register(AnalisePerformance)
class AnalisePerformanceAdmin(admin.ModelAdmin):
    list_display = ['usina', 'data_analise', 'status_performance_badge', 'pr_real_percent', 
                    'energia_gerada_kwh', 'energia_esperada_real_kwh']
    list_filter = ['usina', 'status_performance', 'data_analise']
    search_fields = ['usina__nome', 'justificativa_climatica']
    date_hierarchy = 'data_analise'
    readonly_fields = ['status_performance_badge', 'diferenca_kwh_display', 'diferenca_percent_display',
                       'justificativa_climatica_formatted', 'recomendacoes_formatted']
    
    fieldsets = (
        ('Usina e Data', {
            'fields': ('usina', 'data_analise')
        }),
        ('Energia Gerada vs Esperada', {
            'fields': ('energia_gerada_kwh', 'energia_esperada_ideal_kwh', 
                      'energia_esperada_real_kwh', 'diferenca_kwh_display', 'diferenca_percent_display')
        }),
        ('Performance Ratio', {
            'fields': ('pr_ideal_percent', 'pr_real_percent', 'status_performance_badge')
        }),
        ('Análise Climática', {
            'fields': ('justificativa_climatica_formatted', 'recomendacoes_formatted')
        }),
        ('Perdas Estimadas', {
            'fields': ('perda_temperatura_percent', 'perda_sujeira_percent', 
                      'perda_sombreamento_percent', 'perda_outros_percent'),
            'classes': ('collapse',)
        }),
    )
    
    def status_performance_badge(self, obj):
        cores = {
            'excelente': '#4CAF50',
            'bom': '#8BC34A',
            'aceitavel': '#FFC107',
            'abaixo': '#FF9800',
            'critico': '#F44336'
        }
        icones = {
            'excelente': '🌟',
            'bom': '✅',
            'aceitavel': '⚠️',
            'abaixo': '🔻',
            'critico': '🚨'
        }
        cor = cores.get(obj.status_performance, '#000')
        icone = icones.get(obj.status_performance, '')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{} {}</span>',
            cor, icone, obj.get_status_performance_display()
        )
    status_performance_badge.short_description = 'Status'
    
    def diferenca_kwh_display(self, obj):
        if obj.energia_gerada_kwh and obj.energia_esperada_real_kwh:
            diferenca = obj.energia_gerada_kwh - obj.energia_esperada_real_kwh
            cor = '#4CAF50' if diferenca >= 0 else '#F44336'
            sinal = '+' if diferenca >= 0 else ''
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}{:.2f} kWh</span>',
                cor, sinal, diferenca
            )
        return '-'
    diferenca_kwh_display.short_description = 'Diferença (kWh)'
    
    def diferenca_percent_display(self, obj):
        if obj.energia_gerada_kwh and obj.energia_esperada_real_kwh:
            if obj.energia_esperada_real_kwh > 0:
                diferenca_percent = ((obj.energia_gerada_kwh - obj.energia_esperada_real_kwh) / 
                                   obj.energia_esperada_real_kwh) * 100
                cor = '#4CAF50' if diferenca_percent >= 0 else '#F44336'
                sinal = '+' if diferenca_percent >= 0 else ''
                return format_html(
                    '<span style="color: {}; font-weight: bold;">{}{:.1f}%</span>',
                    cor, sinal, diferenca_percent
                )
        return '-'
    diferenca_percent_display.short_description = 'Diferença (%)'
    
    def justificativa_climatica_formatted(self, obj):
        if obj.justificativa_climatica:
            return format_html('<div style="white-space: pre-wrap; padding: 10px; background: #f5f5f5; border-radius: 5px;">{}</div>', 
                             obj.justificativa_climatica)
        return '-'
    justificativa_climatica_formatted.short_description = 'Justificativa Climática'
    
    def recomendacoes_formatted(self, obj):
        if obj.recomendacoes:
            return format_html('<div style="white-space: pre-wrap; padding: 10px; background: #fff3cd; border-radius: 5px; border-left: 4px solid #ffc107;">{}</div>', 
                             obj.recomendacoes)
        return '-'
    recomendacoes_formatted.short_description = 'Recomendações'
