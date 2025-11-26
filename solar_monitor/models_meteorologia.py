from django.db import models
from django.utils import timezone
from decimal import Decimal


class DadosMeteorologicos(models.Model):
    """Dados meteorológicos para análise de performance das usinas"""
    
    usina = models.ForeignKey(
        'UsinaSolar',
        on_delete=models.CASCADE,
        related_name='dados_meteorologicos',
        verbose_name="Usina"
    )
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Irradiação Solar
    irradiancia_global_w_m2 = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        verbose_name="Irradiância Global (W/m²)",
        help_text="Radiação solar total na superfície"
    )
    irradiancia_direta_w_m2 = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Irradiância Direta (W/m²)"
    )
    irradiancia_difusa_w_m2 = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Irradiância Difusa (W/m²)"
    )
    
    # Temperatura
    temperatura_ar_c = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Temperatura do Ar (°C)"
    )
    sensacao_termica_c = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Sensação Térmica (°C)"
    )
    
    # Condições Atmosféricas
    nebulosidade_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Nebulosidade (%)",
        help_text="% de cobertura de nuvens (0=céu limpo, 100=totalmente nublado)"
    )
    condicao_clima = models.CharField(
        max_length=50,
        choices=[
            ('ceu_limpo', 'Céu Limpo'),
            ('parcialmente_nublado', 'Parcialmente Nublado'),
            ('nublado', 'Nublado'),
            ('chuvoso', 'Chuvoso'),
            ('tempestade', 'Tempestade'),
            ('nevoa', 'Névoa/Neblina'),
        ],
        verbose_name="Condição Climática"
    )
    
    # Precipitação
    precipitacao_mm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Precipitação (mm)",
        help_text="Quantidade de chuva acumulada"
    )
    chovendo = models.BooleanField(
        default=False,
        verbose_name="Está Chovendo"
    )
    
    # Vento
    velocidade_vento_km_h = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Velocidade do Vento (km/h)"
    )
    direcao_vento_graus = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Direção do Vento (°)",
        help_text="0°=Norte, 90°=Leste, 180°=Sul, 270°=Oeste"
    )
    
    # Umidade e Pressão
    umidade_relativa_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Umidade Relativa (%)"
    )
    pressao_atmosferica_hpa = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Pressão Atmosférica (hPa)"
    )
    
    # Visibilidade
    visibilidade_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Visibilidade (km)"
    )
    
    # Índice UV
    indice_uv = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name="Índice UV",
        help_text="Índice de radiação ultravioleta (0-11+)"
    )
    
    # Fonte dos Dados
    fonte_dados = models.CharField(
        max_length=100,
        choices=[
            ('inmet', 'INMET - Instituto Nacional de Meteorologia'),
            ('openweather', 'OpenWeatherMap API'),
            ('weatherapi', 'WeatherAPI'),
            ('sensor_local', 'Sensor Local da Usina'),
            ('manual', 'Inserção Manual'),
        ],
        default='openweather',
        verbose_name="Fonte dos Dados"
    )
    
    # HSP - Horas de Sol Pico (calculado)
    hsp_dia_kwh_m2 = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="HSP do Dia (kWh/m²)",
        help_text="Horas de Sol Pico acumuladas no dia"
    )
    
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Dados Meteorológicos"
        verbose_name_plural = "Dados Meteorológicos"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['usina', '-timestamp']),
            models.Index(fields=['timestamp']),
        ]
        unique_together = ['usina', 'timestamp']

    def __str__(self):
        return f"{self.usina.nome} - {self.timestamp.strftime('%d/%m/%Y %H:%M')} - {self.get_condicao_clima_display()}"

    @property
    def fator_reducao_nuvens(self):
        """Fator de redução de irradiância devido às nuvens"""
        # Céu limpo: 100%, Parcialmente nublado: 70-90%, Nublado: 30-50%, Chuvoso: 10-20%
        nebulosidade = float(self.nebulosidade_percent)
        
        if nebulosidade < 20:
            return 1.0  # 100% - céu limpo
        elif nebulosidade < 50:
            return 0.8  # 80% - poucas nuvens
        elif nebulosidade < 80:
            return 0.5  # 50% - muitas nuvens
        else:
            return 0.2  # 20% - completamente nublado

    @property
    def irradiancia_efetiva_w_m2(self):
        """Irradiância efetiva considerando nebulosidade"""
        return float(self.irradiancia_global_w_m2) * self.fator_reducao_nuvens

    def save(self, *args, **kwargs):
        # Ajustar condição climática baseada em precipitação e nebulosidade
        if self.chovendo or self.precipitacao_mm > 0:
            if self.precipitacao_mm > 10:
                self.condicao_clima = 'tempestade'
            else:
                self.condicao_clima = 'chuvoso'
        elif float(self.nebulosidade_percent) < 20:
            self.condicao_clima = 'ceu_limpo'
        elif float(self.nebulosidade_percent) < 60:
            self.condicao_clima = 'parcialmente_nublado'
        else:
            self.condicao_clima = 'nublado'
        
        super().save(*args, **kwargs)


class AnalisePerformance(models.Model):
    """Análise de performance comparando geração real vs esperada considerando clima"""
    
    usina = models.ForeignKey(
        'UsinaSolar',
        on_delete=models.CASCADE,
        related_name='analises_performance',
        verbose_name="Usina"
    )
    data_analise = models.DateField(verbose_name="Data da Análise")
    
    # Geração Real
    energia_gerada_kwh = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Energia Gerada Real (kWh)"
    )
    
    # Geração Esperada (baseada em irradiância e clima)
    energia_esperada_ideal_kwh = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Energia Esperada - Condições Ideais (kWh)",
        help_text="Geração esperada em céu limpo"
    )
    energia_esperada_real_kwh = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Energia Esperada - Condições Reais (kWh)",
        help_text="Geração esperada considerando clima real"
    )
    
    # Dados Meteorológicos do Dia
    irradiancia_media_w_m2 = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        verbose_name="Irradiância Média (W/m²)"
    )
    hsp_dia_kwh_m2 = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        verbose_name="HSP do Dia (kWh/m²)"
    )
    temperatura_media_c = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Temperatura Média (°C)"
    )
    nebulosidade_media_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Nebulosidade Média (%)"
    )
    precipitacao_total_mm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Precipitação Total (mm)"
    )
    
    # Performance Ratio
    pr_ideal_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="PR vs Ideal (%)",
        help_text="Performance Ratio comparado com condições ideais"
    )
    pr_real_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="PR vs Real (%)",
        help_text="Performance Ratio comparado com condições reais do dia"
    )
    
    # Status da Performance
    status_performance = models.CharField(
        max_length=30,
        choices=[
            ('excelente', 'Excelente (≥95%)'),
            ('bom', 'Bom (85-95%)'),
            ('aceitavel', 'Aceitável (75-85%)'),
            ('abaixo', 'Abaixo do Esperado (60-75%)'),
            ('critico', 'Crítico (<60%)'),
        ],
        verbose_name="Status da Performance"
    )
    
    # Perdas Identificadas
    perda_temperatura_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Perda por Temperatura (%)"
    )
    perda_sujeira_estimada_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Perda por Sujeira Estimada (%)"
    )
    perda_sombreamento_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Perda por Sombreamento (%)"
    )
    
    # Justificativa Climática
    justificativa_climatica = models.TextField(
        blank=True,
        verbose_name="Justificativa Climática",
        help_text="Explicação automática sobre impacto do clima na geração"
    )
    
    # Alertas e Recomendações
    requer_atencao = models.BooleanField(
        default=False,
        verbose_name="Requer Atenção"
    )
    recomendacoes = models.TextField(
        blank=True,
        verbose_name="Recomendações"
    )
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Análise de Performance"
        verbose_name_plural = "Análises de Performance"
        ordering = ['-data_analise']
        unique_together = ['usina', 'data_analise']

    def __str__(self):
        return f"{self.usina.nome} - {self.data_analise} - {self.get_status_performance_display()}"

    def gerar_justificativa_climatica(self):
        """Gera justificativa automática baseada nas condições climáticas"""
        justificativas = []
        
        nebulosidade = float(self.nebulosidade_media_percent)
        chuva = float(self.precipitacao_total_mm)
        temp = float(self.temperatura_media_c)
        
        # Análise de nebulosidade
        if nebulosidade > 70:
            justificativas.append(f"Dia muito nublado ({nebulosidade:.0f}% de nebulosidade), reduzindo significativamente a irradiância solar.")
        elif nebulosidade > 40:
            justificativas.append(f"Nebulosidade moderada ({nebulosidade:.0f}%), afetando a geração solar.")
        elif nebulosidade < 10:
            justificativas.append(f"Céu limpo ({nebulosidade:.0f}% de nuvens), condições ideais para geração.")
        
        # Análise de chuva
        if chuva > 10:
            justificativas.append(f"Chuva intensa ({chuva:.1f}mm), reduzindo drasticamente a irradiância.")
        elif chuva > 0:
            justificativas.append(f"Precipitação de {chuva:.1f}mm impactou a geração.")
        
        # Análise de temperatura
        if temp > 35:
            justificativas.append(f"Temperatura elevada ({temp:.1f}°C) causou perdas por aquecimento dos módulos.")
        elif temp < 15:
            justificativas.append(f"Temperatura amena ({temp:.1f}°C) favoreceu a eficiência dos módulos.")
        
        # Análise de HSP
        hsp = float(self.hsp_dia_kwh_m2)
        if hsp < 3:
            justificativas.append(f"Baixa irradiação solar ({hsp:.2f} HSP), muito abaixo da média regional.")
        elif hsp > 5.5:
            justificativas.append(f"Excelente irradiação solar ({hsp:.2f} HSP), acima da média.")
        
        return " ".join(justificativas) if justificativas else "Condições climáticas dentro do esperado para a região."

    def gerar_recomendacoes(self):
        """Gera recomendações automáticas baseadas na análise"""
        recomendacoes = []
        
        pr_real = float(self.pr_real_percent)
        perda_sujeira = float(self.perda_sujeira_estimada_percent)
        nebulosidade = float(self.nebulosidade_media_percent)
        
        # Recomendações baseadas em PR
        if pr_real < 60:
            recomendacoes.append("⚠️ CRÍTICO: Performance muito abaixo do esperado. Inspeção técnica urgente necessária.")
        elif pr_real < 75:
            recomendacoes.append("⚠️ Performance abaixo do esperado. Verificar possíveis problemas técnicos.")
        elif pr_real >= 95:
            recomendacoes.append("✓ Excelente performance. Sistema operando de forma ótima.")
        
        # Recomendações baseadas em sujeira
        if perda_sujeira > 5:
            recomendacoes.append("🧹 Limpeza dos painéis recomendada (perda estimada por sujeira > 5%).")
        elif perda_sujeira > 3:
            recomendacoes.append("🧹 Considerar limpeza dos painéis em breve.")
        
        # Recomendações baseadas em clima
        if nebulosidade < 20 and pr_real < 85:
            recomendacoes.append("☀️ Céu limpo mas performance baixa. Investigar causas técnicas.")
        
        return " ".join(recomendacoes) if recomendacoes else "Nenhuma ação necessária no momento."

    def save(self, *args, **kwargs):
        # Calcular PR vs Ideal
        if self.energia_esperada_ideal_kwh > 0:
            self.pr_ideal_percent = (self.energia_gerada_kwh / self.energia_esperada_ideal_kwh) * 100
        
        # Calcular PR vs Real (considerando clima)
        if self.energia_esperada_real_kwh > 0:
            self.pr_real_percent = (self.energia_gerada_kwh / self.energia_esperada_real_kwh) * 100
        
        # Determinar status
        pr = float(self.pr_real_percent)
        if pr >= 95:
            self.status_performance = 'excelente'
            self.requer_atencao = False
        elif pr >= 85:
            self.status_performance = 'bom'
            self.requer_atencao = False
        elif pr >= 75:
            self.status_performance = 'aceitavel'
            self.requer_atencao = False
        elif pr >= 60:
            self.status_performance = 'abaixo'
            self.requer_atencao = True
        else:
            self.status_performance = 'critico'
            self.requer_atencao = True
        
        # Gerar justificativa e recomendações
        if not self.justificativa_climatica:
            self.justificativa_climatica = self.gerar_justificativa_climatica()
        
        if not self.recomendacoes:
            self.recomendacoes = self.gerar_recomendacoes()
        
        super().save(*args, **kwargs)
