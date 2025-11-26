from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Inversor, ModeloPlacaSolar, ConfiguracaoPlacasUsina,
    UsinaSolar, LeituraUsina, AlertaUsina, RelatorioMensal
)


@admin.register(Inversor)
class InversorAdmin(admin.ModelAdmin):
    list_display = ['fabricante', 'modelo', 'usina', 'potencia_nominal_kw', 'numero_mppt', 'eficiencia_maxima_percent', 'ativo']
    list_filter = ['fabricante', 'usina', 'ativo', 'numero_mppt']
    search_fields = ['fabricante', 'modelo', 'numero_serie', 'usina__nome']
    readonly_fields = ['criado_em', 'atualizado_em', 'faixa_mppt', 'garantia_ativa']
    
    fieldsets = (
        ('Usina', {
            'fields': ('usina', 'ativo')
        }),
        ('Identificação', {
            'fields': ('fabricante', 'modelo', 'numero_serie')
        }),
        ('Potência', {
            'fields': ('potencia_nominal_kw', 'potencia_maxima_dc_kw')
        }),
        ('Tensão', {
            'fields': (
                'tensao_entrada_min_v', 'tensao_entrada_max_v',
                'tensao_mppt_min_v', 'tensao_mppt_max_v', 'faixa_mppt',
                'tensao_saida_v'
            )
        }),
        ('Corrente', {
            'fields': ('corrente_entrada_max_a', 'corrente_saida_max_a')
        }),
        ('Eficiência e MPPT', {
            'fields': (
                'eficiencia_maxima_percent', 'eficiencia_europeia_percent',
                'numero_mppt', 'strings_por_mppt'
            )
        }),
        ('Proteções', {
            'fields': ('grau_protecao_ip', 'certificacoes'),
            'classes': ('collapse',)
        }),
        ('Condições Operacionais', {
            'fields': (
                'temperatura_operacao_min_c', 'temperatura_operacao_max_c',
                'altitude_maxima_m'
            ),
            'classes': ('collapse',)
        }),
        ('Comunicação', {
            'fields': ('tipo_comunicacao', 'api_endpoint', 'api_key'),
            'classes': ('collapse',)
        }),
        ('Instalação e Garantia', {
            'fields': (
                'data_fabricacao', 'data_instalacao',
                'anos_garantia', 'garantia_ativa'
            ),
            'classes': ('collapse',)
        }),
        ('Físico', {
            'fields': ('peso_kg', 'dimensoes'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ModeloPlacaSolar)
class ModeloPlacaSolarAdmin(admin.ModelAdmin):
    list_display = ['fabricante', 'modelo', 'potencia_pico_wp', 'eficiencia_percent', 'tecnologia', 'bifacial', 'ativo']
    list_filter = ['fabricante', 'tecnologia', 'bifacial', 'ativo']
    search_fields = ['fabricante', 'modelo']
    readonly_fields = ['criado_em', 'atualizado_em', 'area_m2', 'potencia_por_m2']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('fabricante', 'modelo', 'ativo')
        }),
        ('Especificações Elétricas (STC)', {
            'fields': (
                'potencia_pico_wp',
                'tensao_circuito_aberto_voc', 'corrente_curto_circuito_isc',
                'tensao_maxima_potencia_vmp', 'corrente_maxima_potencia_imp'
            )
        }),
        ('Tecnologia e Eficiência', {
            'fields': (
                'tecnologia', 'eficiencia_percent',
                'bifacial', 'bifacialidade_percent'
            )
        }),
        ('Coeficientes de Temperatura', {
            'fields': (
                'coef_temp_potencia_percent',
                'coef_temp_tensao_percent',
                'coef_temp_corrente_percent'
            ),
            'classes': ('collapse',)
        }),
        ('Dimensões', {
            'fields': (
                'comprimento_mm', 'largura_mm', 'espessura_mm',
                'peso_kg', 'area_m2', 'potencia_por_m2'
            )
        }),
        ('Células e Tolerância', {
            'fields': ('numero_celulas', 'tolerancia_potencia_percent'),
            'classes': ('collapse',)
        }),
        ('Condições Operacionais', {
            'fields': (
                'temperatura_operacao_min_c', 'temperatura_operacao_max_c',
                'tensao_maxima_sistema_v'
            ),
            'classes': ('collapse',)
        }),
        ('Garantias', {
            'fields': (
                'anos_garantia_produto', 'anos_garantia_performance',
                'garantia_performance_25anos_percent', 'certificacoes'
            ),
            'classes': ('collapse',)
        }),
        ('Informações Adicionais', {
            'fields': ('observacoes', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


class ConfiguracaoPlacasInline(admin.TabularInline):
    model = ConfiguracaoPlacasUsina
    extra = 0
    fields = ['modelo_placa', 'quantidade_placas', 'quantidade_strings', 'placas_por_string', 'inversor', 'data_instalacao', 'ativa']
    readonly_fields = []


class InversoresInline(admin.TabularInline):
    model = Inversor
    extra = 0
    fields = ['fabricante', 'modelo', 'potencia_nominal_kw', 'numero_mppt', 'eficiencia_maxima_percent', 'ativo']
    readonly_fields = []
    verbose_name = "Inversor"
    verbose_name_plural = "Inversores da Usina"


@admin.register(ConfiguracaoPlacasUsina)
class ConfiguracaoPlacasUsinaAdmin(admin.ModelAdmin):
    list_display = ['usina', 'modelo_placa', 'quantidade_placas', 'potencia_total_kwp_display', 'inversor', 'data_instalacao', 'ativa']
    list_filter = ['usina', 'modelo_placa__fabricante', 'tipo_instalacao', 'tem_rastreamento', 'ativa']
    search_fields = ['usina__nome', 'modelo_placa__modelo']
    readonly_fields = ['criado_em', 'atualizado_em', 'potencia_total_kwp', 'area_total_m2', 'tensao_string_voc', 'tensao_string_vmp']
    
    fieldsets = (
        ('Usina e Modelo', {
            'fields': ('usina', 'modelo_placa', 'ativa')
        }),
        ('Quantidade e Arranjo', {
            'fields': (
                'quantidade_placas', 'quantidade_strings', 'placas_por_string',
                'potencia_total_kwp', 'area_total_m2'
            )
        }),
        ('Orientação e Instalação', {
            'fields': (
                'orientacao_azimutal', 'inclinacao_graus',
                'tipo_instalacao', 'sombreamento_estimado_percent'
            )
        }),
        ('Rastreamento Solar', {
            'fields': ('tem_rastreamento', 'tipo_rastreamento'),
            'classes': ('collapse',)
        }),
        ('Conexão Elétrica', {
            'fields': (
                'inversor', 'mppt_utilizado',
                'tensao_string_voc', 'tensao_string_vmp'
            )
        }),
        ('Instalação', {
            'fields': ('data_instalacao', 'observacoes'),
            'classes': ('collapse',)
        }),
        ('Informações do Sistema', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def potencia_total_kwp_display(self, obj):
        return f"{obj.potencia_total_kwp:.2f} kWp"
    potencia_total_kwp_display.short_description = 'Potência Total'


@admin.register(UsinaSolar)
class UsinaSolarAdmin(admin.ModelAdmin):
    list_display = ['nome', 'localizacao', 'capacidade_kwp', 'quantidade_inversores_display', 'quantidade_placas_display', 'status_badge', 'ultima_leitura_display']
    list_filter = ['ativa', 'data_instalacao']
    search_fields = ['nome', 'localizacao']
    readonly_fields = ['criado_em', 'atualizado_em', 'geracao_total_display', 'quantidade_total_placas', 'area_total_m2', 'fator_dimensionamento', 'potencia_total_inversores_kw', 'quantidade_inversores']
    inlines = [InversoresInline, ConfiguracaoPlacasInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'localizacao', 'capacidade_kwp', 'ativa')
        }),
        ('Localização GPS', {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ('Inversores', {
            'fields': ('quantidade_inversores', 'potencia_total_inversores_kw', 'fator_dimensionamento')
        }),
        ('Placas Solares', {
            'fields': ('quantidade_total_placas', 'area_total_m2'),
        }),
        ('Outras Informações', {
            'fields': ('data_instalacao', 'criado_em', 'atualizado_em', 'geracao_total_display'),
            'classes': ('collapse',)
        }),
    )
    
    def quantidade_inversores_display(self, obj):
        qtd = obj.quantidade_inversores
        potencia = obj.potencia_total_inversores_kw
        return f"{qtd} inv. ({potencia:.1f}kW)"
    quantidade_inversores_display.short_description = 'Inversores'
    
    def quantidade_placas_display(self, obj):
        return f"{obj.quantidade_total_placas} placas"
    quantidade_placas_display.short_description = 'Qtd Placas'
    
    def status_badge(self, obj):
        if not obj.ativa:
            return format_html('<span style="color: gray;">● Inativa</span>')
        
        ultima = obj.ultima_leitura
        if not ultima:
            return format_html('<span style="color: orange;">● Sem Dados</span>')
        
        if ultima.status == 'online':
            return format_html('<span style="color: green;">● Online</span>')
        elif ultima.status == 'offline':
            return format_html('<span style="color: red;">● Offline</span>')
        elif ultima.status == 'alerta':
            return format_html('<span style="color: orange;">⚠ Alerta</span>')
        else:
            return format_html(f'<span style="color: gray;">● {ultima.get_status_display()}</span>')
    
    status_badge.short_description = 'Status'
    
    def ultima_leitura_display(self, obj):
        ultima = obj.ultima_leitura
        if not ultima:
            return "—"
        return f"{ultima.potencia_atual_kw} kW ({ultima.timestamp.strftime('%d/%m %H:%M')})"
    
    ultima_leitura_display.short_description = 'Última Leitura'
    
    def geracao_total_display(self, obj):
        total = obj.geracao_total
        return f"{total:,.2f} kWh"
    
    geracao_total_display.short_description = 'Geração Total'


@admin.register(LeituraUsina)
class LeituraUsinaAdmin(admin.ModelAdmin):
    list_display = ['usina', 'timestamp', 'potencia_atual_kw', 'energia_dia_kwh', 'status_badge', 'eficiencia_percent']
    list_filter = ['usina', 'status', 'timestamp']
    search_fields = ['usina__nome']
    readonly_fields = ['timestamp', 'co2_evitado_kg', 'economia_reais']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Usina e Timestamp', {
            'fields': ('usina', 'timestamp', 'status')
        }),
        ('Geração de Energia', {
            'fields': ('potencia_atual_kw', 'energia_gerada_kwh', 'energia_dia_kwh')
        }),
        ('Dados Ambientais', {
            'fields': ('irradiancia_w_m2', 'temperatura_modulo_c', 'temperatura_ambiente_c'),
            'classes': ('collapse',)
        }),
        ('Sistema Elétrico', {
            'fields': ('tensao_v', 'corrente_a', 'frequencia_hz'),
            'classes': ('collapse',)
        }),
        ('Performance', {
            'fields': ('eficiencia_percent', 'fator_potencia')
        }),
        ('Sustentabilidade', {
            'fields': ('co2_evitado_kg', 'economia_reais'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'online': 'green',
            'offline': 'red',
            'manutencao': 'blue',
            'alerta': 'orange',
            'erro': 'darkred'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(f'<span style="color: {color};">● {obj.get_status_display()}</span>')
    
    status_badge.short_description = 'Status'


@admin.register(AlertaUsina)
class AlertaUsinaAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'usina', 'tipo_badge', 'categoria', 'titulo', 'resolvido_badge']
    list_filter = ['tipo', 'categoria', 'resolvido', 'usina']
    search_fields = ['titulo', 'descricao', 'usina__nome']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Alerta', {
            'fields': ('usina', 'timestamp', 'tipo', 'categoria', 'titulo', 'descricao')
        }),
        ('Resolução', {
            'fields': ('resolvido', 'resolvido_em', 'observacoes_resolucao')
        }),
    )
    
    def tipo_badge(self, obj):
        colors = {
            'info': '#17a2b8',
            'aviso': '#ffc107',
            'alerta': '#ff9800',
            'critico': '#dc3545'
        }
        icons = {
            'info': 'ℹ',
            'aviso': '⚠',
            'alerta': '⚠',
            'critico': '🔴'
        }
        color = colors.get(obj.tipo, 'gray')
        icon = icons.get(obj.tipo, '●')
        return format_html(f'<span style="color: {color}; font-weight: bold;">{icon} {obj.get_tipo_display()}</span>')
    
    tipo_badge.short_description = 'Tipo'
    
    def resolvido_badge(self, obj):
        if obj.resolvido:
            return format_html('<span style="color: green;">✓ Resolvido</span>')
        return format_html('<span style="color: orange;">⏳ Pendente</span>')
    
    resolvido_badge.short_description = 'Status'
    
    actions = ['marcar_resolvido']
    
    def marcar_resolvido(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(resolvido=True, resolvido_em=timezone.now())
        self.message_user(request, f'{count} alerta(s) marcado(s) como resolvido(s).')
    
    marcar_resolvido.short_description = "Marcar como resolvido"


@admin.register(RelatorioMensal)
class RelatorioMensalAdmin(admin.ModelAdmin):
    list_display = ['usina', 'periodo_display', 'energia_gerada_total_kwh', 'energia_media_dia_kwh', 'eficiencia_media_percent', 'economia_total_reais']
    list_filter = ['usina', 'ano', 'mes']
    search_fields = ['usina__nome']
    readonly_fields = ['criado_em']
    
    fieldsets = (
        ('Período', {
            'fields': ('usina', 'mes', 'ano')
        }),
        ('Geração de Energia', {
            'fields': ('energia_gerada_total_kwh', 'energia_media_dia_kwh', 'potencia_pico_kw', 'horas_sol_pico')
        }),
        ('Sustentabilidade', {
            'fields': ('co2_evitado_total_kg', 'economia_total_reais')
        }),
        ('Performance', {
            'fields': ('eficiencia_media_percent', 'dias_offline')
        }),
        ('Informações', {
            'fields': ('criado_em',),
            'classes': ('collapse',)
        }),
    )
    
    def periodo_display(self, obj):
        meses = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        return f"{meses[obj.mes]}/{obj.ano}"
    
    periodo_display.short_description = 'Período'


@admin.register(DadosMeteorologicos)
class DadosMeteorologicosAdmin(admin.ModelAdmin):
    list_display = ['usina', 'timestamp', 'condicao_clima_badge', 'irradiancia_global_w_m2', 'temperatura_ar_c', 'nebulosidade_percent', 'precipitacao_mm', 'fonte_dados']
    list_filter = ['usina', 'condicao_clima', 'fonte_dados', 'timestamp']
    search_fields = ['usina__nome']
    date_hierarchy = 'timestamp'
    readonly_fields = ['hsp_dia_kwh_m2_display', 'indice_claridade_display']
    
    fieldsets = (
        ('Usina e Timestamp', {
            'fields': ('usina', 'timestamp', 'fonte_dados')
        }),
        ('Irradiação Solar', {
            'fields': ('irradiancia_global_w_m2', 'irradiancia_direta_w_m2', 'irradiancia_difusa_w_m2', 'hsp_dia_kwh_m2_display', 'indice_claridade_display')
        }),
        ('Condições Clim�ticas', {
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
        from django.utils.html import format_html
        cores = {
            'ceu_limpo': '#4CAF50',
            'parcialmente_nublado': '#2196F3',
            'nublado': '#9E9E9E',
            'chuvoso': '#FF9800',
            'tempestade': '#F44336',
            'nevoa': '#607D8B'
        }
        icones = {
            'ceu_limpo': '��',
            'parcialmente_nublado': '�',
            'nublado': '��',
            'chuvoso': 'g����',
            'tempestade': '�',
            'nevoa': 'g���'
        }
        cor = cores.get(obj.condicao_clima, '#000')
