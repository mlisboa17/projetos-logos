from django.db import models
from django.utils import timezone
from decimal import Decimal


class Inversor(models.Model):
    """Inversor Solar - Equipamento que converte corrente contínua (DC) em alternada (AC)"""
    
    # Relacionamento com Usina
    usina = models.ForeignKey(
        'UsinaSolar',
        on_delete=models.CASCADE,
        related_name='inversores',
        verbose_name="Usina",
        help_text="Usina à qual este inversor pertence"
    )
    
    # Identificação
    fabricante = models.CharField(max_length=100, verbose_name="Fabricante")
    modelo = models.CharField(max_length=150, verbose_name="Modelo")
    numero_serie = models.CharField(max_length=200, blank=True, verbose_name="Número de Série")
    
    # Especificações Técnicas de Potência
    potencia_nominal_kw = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Potência Nominal (kW)",
        help_text="Potência máxima de saída do inversor"
    )
    potencia_maxima_dc_kw = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Potência Máxima DC (kW)",
        help_text="Potência máxima que pode receber dos painéis"
    )
    
    # Especificações de Tensão
    tensao_entrada_min_v = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        verbose_name="Tensão de Entrada Mínima (V)"
    )
    tensao_entrada_max_v = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        verbose_name="Tensão de Entrada Máxima (V)"
    )
    tensao_mppt_min_v = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        verbose_name="Tensão MPPT Mínima (V)",
        help_text="Faixa MPPT - Maximum Power Point Tracking"
    )
    tensao_mppt_max_v = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        verbose_name="Tensão MPPT Máxima (V)"
    )
    tensao_saida_v = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('220.00'),
        verbose_name="Tensão de Saída (V)",
        help_text="Tensão AC de saída (220V, 380V, etc.)"
    )
    
    # Especificações de Corrente
    corrente_entrada_max_a = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        verbose_name="Corrente de Entrada Máxima (A)"
    )
    corrente_saida_max_a = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        verbose_name="Corrente de Saída Máxima (A)"
    )
    
    # Performance e Eficiência
    eficiencia_maxima_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('97.00'),
        verbose_name="Eficiência Máxima (%)",
        help_text="Eficiência de conversão DC para AC"
    )
    eficiencia_europeia_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Eficiência Europeia (%)",
        help_text="Média ponderada de eficiência"
    )
    
    # Configuração MPPT
    numero_mppt = models.IntegerField(
        verbose_name="Número de MPPTs",
        help_text="Rastreadores de ponto de máxima potência"
    )
    strings_por_mppt = models.IntegerField(
        verbose_name="Strings por MPPT",
        help_text="Quantas strings podem ser conectadas por MPPT"
    )
    
    # Proteções e Certificações
    grau_protecao_ip = models.CharField(
        max_length=10,
        default='IP65',
        verbose_name="Grau de Proteção IP",
        help_text="Ex: IP65 (proteção contra poeira e jatos d'água)"
    )
    certificacoes = models.TextField(
        blank=True,
        verbose_name="Certificações",
        help_text="Ex: INMETRO, IEC 62109, VDE, etc."
    )
    
    # Condições Operacionais
    temperatura_operacao_min_c = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal('-25.0'),
        verbose_name="Temperatura Operação Mínima (°C)"
    )
    temperatura_operacao_max_c = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal('60.0'),
        verbose_name="Temperatura Operação Máxima (°C)"
    )
    altitude_maxima_m = models.IntegerField(
        default=2000,
        verbose_name="Altitude Máxima (m)",
        help_text="Altitude máxima de operação sem desrating"
    )
    
    # Comunicação e Monitoramento
    tipo_comunicacao = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Tipo de Comunicação",
        help_text="Ex: Wi-Fi, Ethernet, RS485, Modbus"
    )
    api_endpoint = models.URLField(
        blank=True,
        verbose_name="Endpoint da API",
        help_text="URL base da API do fabricante"
    )
    api_key = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Chave da API"
    )
    
    # Garantia e Instalação
    data_fabricacao = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Fabricação"
    )
    data_instalacao = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Instalação"
    )
    anos_garantia = models.IntegerField(
        default=5,
        verbose_name="Anos de Garantia"
    )
    
    # Dimensões e Peso
    peso_kg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Peso (kg)"
    )
    dimensoes = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Dimensões (LxAxP mm)"
    )
    
    # Observações
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )
    
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Inversor"
        verbose_name_plural = "Inversores"
        ordering = ['fabricante', 'modelo']

    def __str__(self):
        return f"{self.fabricante} {self.modelo} - {self.potencia_nominal_kw}kW"

    @property
    def capacidade_total(self):
        """Capacidade total em kW considerando potência nominal"""
        return self.potencia_nominal_kw

    @property
    def faixa_mppt(self):
        """Retorna a faixa de tensão MPPT"""
        return f"{self.tensao_mppt_min_v}V - {self.tensao_mppt_max_v}V"

    @property
    def garantia_ativa(self):
        """Verifica se a garantia ainda está ativa"""
        if not self.data_instalacao:
            return None
        from datetime import date
        anos_passados = (date.today() - self.data_instalacao).days / 365.25
        return anos_passados < self.anos_garantia


class ModeloPlacaSolar(models.Model):
    """Modelo de Placa Solar (Painel Fotovoltaico)"""
    
    # Identificação
    fabricante = models.CharField(max_length=100, verbose_name="Fabricante")
    modelo = models.CharField(max_length=150, verbose_name="Modelo")
    
    # Especificações Elétricas (STC - Standard Test Conditions: 1000W/m², 25°C, AM1.5)
    potencia_pico_wp = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        verbose_name="Potência Pico (Wp)",
        help_text="Potência em condições padrão de teste"
    )
    tensao_circuito_aberto_voc = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Tensão Circuito Aberto Voc (V)"
    )
    corrente_curto_circuito_isc = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Corrente Curto-Circuito Isc (A)"
    )
    tensao_maxima_potencia_vmp = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Tensão Máxima Potência Vmp (V)",
        help_text="Tensão no ponto de máxima potência"
    )
    corrente_maxima_potencia_imp = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Corrente Máxima Potência Imp (A)"
    )
    
    # Eficiência e Tecnologia
    eficiencia_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Eficiência (%)",
        help_text="Eficiência de conversão solar para elétrica"
    )
    tecnologia = models.CharField(
        max_length=50,
        choices=[
            ('monocristalino', 'Monocristalino'),
            ('policristalino', 'Policristalino'),
            ('filme_fino', 'Filme Fino'),
            ('perc', 'PERC (Passivated Emitter Rear Cell)'),
            ('hjt', 'HJT (Heterojunction)'),
            ('topcon', 'TOPCon'),
            ('bifacial', 'Bifacial'),
        ],
        verbose_name="Tecnologia"
    )
    
    # Coeficientes de Temperatura (importantes para calcular performance em diferentes temperaturas)
    coef_temp_potencia_percent = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        default=Decimal('-0.400'),
        verbose_name="Coef. Temperatura Potência (%/°C)",
        help_text="Perda de potência por °C acima de 25°C (geralmente negativo)"
    )
    coef_temp_tensao_percent = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="Coef. Temperatura Tensão (%/°C)"
    )
    coef_temp_corrente_percent = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name="Coef. Temperatura Corrente (%/°C)"
    )
    
    # Especificações Mecânicas
    comprimento_mm = models.IntegerField(verbose_name="Comprimento (mm)")
    largura_mm = models.IntegerField(verbose_name="Largura (mm)")
    espessura_mm = models.IntegerField(default=40, verbose_name="Espessura (mm)")
    peso_kg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Peso (kg)"
    )
    
    # Número de Células
    numero_celulas = models.IntegerField(
        verbose_name="Número de Células",
        help_text="Ex: 60, 72, 120, 144 células"
    )
    
    # Tolerância de Potência
    tolerancia_potencia_percent = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('3.00'),
        verbose_name="Tolerância de Potência (±%)"
    )
    
    # Condições Operacionais
    temperatura_operacao_min_c = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal('-40.0'),
        verbose_name="Temperatura Operação Mínima (°C)"
    )
    temperatura_operacao_max_c = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal('85.0'),
        verbose_name="Temperatura Operação Máxima (°C)"
    )
    tensao_maxima_sistema_v = models.IntegerField(
        default=1000,
        verbose_name="Tensão Máxima do Sistema (V)",
        help_text="Tensão máxima DC suportada"
    )
    
    # Certificações
    certificacoes = models.TextField(
        blank=True,
        verbose_name="Certificações",
        help_text="Ex: INMETRO, IEC 61215, IEC 61730"
    )
    
    # Garantias
    anos_garantia_produto = models.IntegerField(
        default=10,
        verbose_name="Anos Garantia Produto"
    )
    anos_garantia_performance = models.IntegerField(
        default=25,
        verbose_name="Anos Garantia Performance"
    )
    garantia_performance_25anos_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('80.00'),
        verbose_name="Garantia Performance 25 anos (%)",
        help_text="% da potência original garantida após 25 anos"
    )
    
    # Dados Adicionais
    bifacial = models.BooleanField(
        default=False,
        verbose_name="Bifacial",
        help_text="Gera energia pelos dois lados"
    )
    bifacialidade_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Bifacialidade (%)",
        help_text="% de geração da face traseira em relação à frontal"
    )
    
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Modelo de Placa Solar"
        verbose_name_plural = "Modelos de Placas Solares"
        ordering = ['fabricante', 'modelo']

    def __str__(self):
        return f"{self.fabricante} {self.modelo} - {self.potencia_pico_wp}Wp"

    @property
    def area_m2(self):
        """Área do painel em m²"""
        return (self.comprimento_mm * self.largura_mm) / 1_000_000

    @property
    def potencia_por_m2(self):
        """Potência por m² (W/m²)"""
        area = self.area_m2
        return float(self.potencia_pico_wp) / area if area > 0 else 0


class ConfiguracaoPlacasUsina(models.Model):
    """Configuração das placas instaladas em cada usina"""
    
    usina = models.ForeignKey(
        'UsinaSolar',
        on_delete=models.CASCADE,
        related_name='configuracoes_placas',
        verbose_name="Usina"
    )
    modelo_placa = models.ForeignKey(
        ModeloPlacaSolar,
        on_delete=models.PROTECT,
        related_name='instalacoes',
        verbose_name="Modelo da Placa"
    )
    
    # Quantidade e Arranjo
    quantidade_placas = models.IntegerField(
        verbose_name="Quantidade de Placas",
        help_text="Número total de placas deste modelo"
    )
    quantidade_strings = models.IntegerField(
        verbose_name="Número de Strings",
        help_text="Strings são conjuntos de placas em série"
    )
    placas_por_string = models.IntegerField(
        verbose_name="Placas por String",
        help_text="Quantidade de placas conectadas em série em cada string"
    )
    
    # Orientação e Inclinação
    orientacao_azimutal = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Orientação Azimutal (°)",
        help_text="0°=Norte, 90°=Leste, 180°=Sul, 270°=Oeste"
    )
    inclinacao_graus = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name="Inclinação (°)",
        help_text="Ângulo de inclinação dos painéis (0° horizontal, 90° vertical)"
    )
    
    # Tipo de Instalação
    tipo_instalacao = models.CharField(
        max_length=50,
        choices=[
            ('telhado', 'Telhado'),
            ('solo', 'Solo (Ground Mount)'),
            ('carport', 'Carport'),
            ('fachada', 'Fachada'),
            ('tracker', 'Tracker (Seguidor Solar)'),
        ],
        default='telhado',
        verbose_name="Tipo de Instalação"
    )
    
    # Rastreamento (se aplicável)
    tem_rastreamento = models.BooleanField(
        default=False,
        verbose_name="Tem Rastreamento Solar",
        help_text="Sistema de tracker que acompanha o movimento do sol"
    )
    tipo_rastreamento = models.CharField(
        max_length=30,
        choices=[
            ('nenhum', 'Nenhum'),
            ('eixo_unico_horizontal', 'Eixo Único Horizontal'),
            ('eixo_unico_vertical', 'Eixo Único Vertical'),
            ('dois_eixos', 'Dois Eixos'),
        ],
        default='nenhum',
        verbose_name="Tipo de Rastreamento"
    )
    
    # Conexão ao Inversor
    inversor = models.ForeignKey(
        Inversor,
        on_delete=models.PROTECT,
        related_name='configuracoes_placas',
        null=True,
        blank=True,
        verbose_name="Inversor Conectado",
        help_text="Inversor ao qual estas placas estão conectadas"
    )
    mppt_utilizado = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="MPPT Utilizado",
        help_text="Número do MPPT do inversor ao qual está conectado"
    )
    
    # Sombreamento
    sombreamento_estimado_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Sombreamento Estimado (%)",
        help_text="% de perda estimada por sombreamento"
    )
    
    # Data de Instalação
    data_instalacao = models.DateField(
        verbose_name="Data de Instalação"
    )
    
    # Status
    ativa = models.BooleanField(default=True, verbose_name="Configuração Ativa")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração de Placas"
        verbose_name_plural = "Configurações de Placas"
        ordering = ['-data_instalacao']

    def __str__(self):
        return f"{self.usina.nome} - {self.quantidade_placas}x {self.modelo_placa.modelo}"

    @property
    def potencia_total_wp(self):
        """Potência total desta configuração em Wp"""
        return self.quantidade_placas * self.modelo_placa.potencia_pico_wp

    @property
    def potencia_total_kwp(self):
        """Potência total desta configuração em kWp"""
        return float(self.potencia_total_wp) / 1000

    @property
    def area_total_m2(self):
        """Área total ocupada pelas placas em m²"""
        return self.quantidade_placas * self.modelo_placa.area_m2

    @property
    def tensao_string_voc(self):
        """Tensão de circuito aberto de uma string"""
        return self.placas_por_string * self.modelo_placa.tensao_circuito_aberto_voc

    @property
    def tensao_string_vmp(self):
        """Tensão de máxima potência de uma string"""
        return self.placas_por_string * self.modelo_placa.tensao_maxima_potencia_vmp

    def clean(self):
        """Validações"""
        from django.core.exceptions import ValidationError
        
        # Verificar se quantidade de placas = strings × placas_por_string
        if self.quantidade_placas != (self.quantidade_strings * self.placas_por_string):
            raise ValidationError(
                f"Quantidade de placas ({self.quantidade_placas}) deve ser igual a "
                f"strings ({self.quantidade_strings}) × placas por string ({self.placas_por_string})"
            )
        
        # Verificar se a tensão está dentro da faixa MPPT do inversor
        if self.inversor:
            tensao_vmp = float(self.tensao_string_vmp)
            if tensao_vmp < float(self.inversor.tensao_mppt_min_v):
                raise ValidationError(
                    f"Tensão Vmp da string ({tensao_vmp}V) está abaixo da faixa MPPT do inversor "
                    f"({self.inversor.tensao_mppt_min_v}V - {self.inversor.tensao_mppt_max_v}V)"
                )
            if tensao_vmp > float(self.inversor.tensao_mppt_max_v):
                raise ValidationError(
                    f"Tensão Vmp da string ({tensao_vmp}V) está acima da faixa MPPT do inversor "
                    f"({self.inversor.tensao_mppt_min_v}V - {self.inversor.tensao_mppt_max_v}V)"
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class UsinaSolar(models.Model):
    """Usina Solar do Grupo Lisboa"""
    nome = models.CharField(max_length=200, verbose_name="Nome da Usina")
    localizacao = models.CharField(max_length=300, verbose_name="Localização")
    capacidade_kwp = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Capacidade Instalada (kWp)",
        help_text="Soma da potência de todas as placas instaladas"
    )
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        verbose_name="Latitude",
        help_text="Coordenada GPS - Latitude (ex: -8.047562)"
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        verbose_name="Longitude",
        help_text="Coordenada GPS - Longitude (ex: -34.877001)"
    )
    altitude_m = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Altitude (m)",
        help_text="Altitude em metros acima do nível do mar"
    )
    
    # Informações Regionais para Análise Climática
    cidade = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Cidade"
    )
    estado = models.CharField(
        max_length=2,
        blank=True,
        verbose_name="Estado (UF)",
        help_text="Ex: PE, SP, RJ"
    )
    cep = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="CEP"
    )
    
    # Dados Climatológicos da Região (médias anuais)
    irradiancia_media_anual_kwh_m2_dia = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Irradiância Média Anual (kWh/m²/dia)",
        help_text="HSP médio anual da região (ex: Recife ≈ 5.2)"
    )
    temperatura_media_anual_c = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name="Temperatura Média Anual (°C)",
        help_text="Temperatura média da região"
    )
    
    # Estação Meteorológica Mais Próxima
    estacao_meteo_codigo = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Código Estação Meteorológica",
        help_text="Código INMET da estação mais próxima"
    )
    estacao_meteo_nome = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Nome Estação Meteorológica"
    )
    distancia_estacao_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Distância da Estação (km)"
    )
    
    data_instalacao = models.DateField(verbose_name="Data de Instalação")
    ativa = models.BooleanField(default=True, verbose_name="Usina Ativa")
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Usina Solar"
        verbose_name_plural = "Usinas Solares"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.capacidade_kwp}kWp"

    @property
    def geracao_total(self):
        """Total de energia gerada (kWh)"""
        return self.leituras.aggregate(
            total=models.Sum('energia_gerada_kwh')
        )['total'] or 0

    @property
    def ultima_leitura(self):
        """Última leitura registrada"""
        return self.leituras.order_by('-timestamp').first()

    @property
    def quantidade_total_placas(self):
        """Quantidade total de placas instaladas"""
        return self.configuracoes_placas.filter(ativa=True).aggregate(
            total=models.Sum('quantidade_placas')
        )['total'] or 0

    @property
    def area_total_m2(self):
        """Área total ocupada pelas placas em m²"""
        total = 0
        for config in self.configuracoes_placas.filter(ativa=True):
            total += config.area_total_m2
        return total

    @property
    def inversores_ativos(self):
        """Lista de inversores ativos da usina"""
        return self.inversores.filter(ativo=True)

    @property
    def quantidade_inversores(self):
        """Quantidade de inversores ativos"""
        return self.inversores.filter(ativo=True).count()

    @property
    def potencia_total_inversores_kw(self):
        """Potência total nominal de todos os inversores da usina"""
        total = self.inversores.filter(ativo=True).aggregate(
            total=models.Sum('potencia_nominal_kw')
        )['total'] or 0
        return float(total)

    @property
    def fator_dimensionamento(self):
        """Fator de dimensionamento DC/AC (sobrecarga dos inversores)"""
        potencia_ac = self.potencia_total_inversores_kw
        if potencia_ac == 0:
            return None
        potencia_dc = float(self.capacidade_kwp)
        return potencia_dc / potencia_ac

    @property
    def performance_ratio_esperado(self):
        """Performance Ratio esperado (considerando perdas típicas)"""
        # PR típico = 75-85% (perdas por temperatura, cabeamento, sujeira, etc.)
        pr_base = Decimal('0.80')  # 80%
        
        # Reduzir por sombreamento
        sombreamento_total = 0
        configs = self.configuracoes_placas.filter(ativa=True)
        if configs.exists():
            sombreamento_total = configs.aggregate(
                media=models.Avg('sombreamento_estimado_percent')
            )['media'] or 0
        
        pr_ajustado = pr_base * (1 - (Decimal(str(sombreamento_total)) / 100))
        return float(pr_ajustado)

    def calcular_geracao_esperada_kwh(self, irradiancia_media_kwh_m2_dia):
        """
        Calcula geração esperada diária
        
        Args:
            irradiancia_media_kwh_m2_dia: Irradiância solar média em kWh/m²/dia (HSP - Horas de Sol Pico)
        
        Returns:
            Energia esperada em kWh/dia
        """
        # Fórmula: E = P × HSP × PR
        # E = Energia (kWh), P = Potência pico (kWp), HSP = Horas de Sol Pico, PR = Performance Ratio
        energia_esperada = float(self.capacidade_kwp) * irradiancia_media_kwh_m2_dia * self.performance_ratio_esperado
        return round(energia_esperada, 2)

    def verificar_performance(self, energia_gerada_kwh, irradiancia_media_kwh_m2_dia):
        """
        Verifica se a performance está adequada
        
        Returns:
            dict com status e percentual de performance
        """
        energia_esperada = self.calcular_geracao_esperada_kwh(irradiancia_media_kwh_m2_dia)
        
        if energia_esperada == 0:
            return {'status': 'sem_dados', 'percentual': 0, 'energia_esperada': 0}
        
        percentual = (energia_gerada_kwh / energia_esperada) * 100
        
        if percentual >= 90:
            status = 'excelente'
        elif percentual >= 75:
            status = 'bom'
        elif percentual >= 60:
            status = 'abaixo_esperado'
        else:
            status = 'critico'
        
        return {
            'status': status,
            'percentual': round(percentual, 1),
            'energia_esperada': energia_esperada,
            'energia_real': energia_gerada_kwh,
            'diferenca': round(energia_gerada_kwh - energia_esperada, 2)
        }


class LeituraUsina(models.Model):
    """Leitura em tempo real da usina solar"""
    usina = models.ForeignKey(
        UsinaSolar, 
        on_delete=models.CASCADE, 
        related_name='leituras'
    )
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Dados de geração
    potencia_atual_kw = models.DecimalField(
        max_digits=10, 
        decimal_places=3,
        verbose_name="Potência Atual (kW)"
    )
    energia_gerada_kwh = models.DecimalField(
        max_digits=12, 
        decimal_places=3,
        verbose_name="Energia Gerada Acumulada (kWh)"
    )
    energia_dia_kwh = models.DecimalField(
        max_digits=10, 
        decimal_places=3,
        default=0,
        verbose_name="Energia do Dia (kWh)"
    )
    
    # Dados ambientais
    irradiancia_w_m2 = models.DecimalField(
        max_digits=7, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Irradiância (W/m²)"
    )
    temperatura_modulo_c = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Temperatura do Módulo (°C)"
    )
    temperatura_ambiente_c = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Temperatura Ambiente (°C)"
    )
    
    # Status do sistema
    tensao_v = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Tensão (V)"
    )
    corrente_a = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Corrente (A)"
    )
    frequencia_hz = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Frequência (Hz)"
    )
    
    # Performance
    eficiencia_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Eficiência (%)"
    )
    fator_potencia = models.DecimalField(
        max_digits=4, 
        decimal_places=3, 
        null=True, 
        blank=True,
        verbose_name="Fator de Potência"
    )
    
    # Economia e sustentabilidade
    co2_evitado_kg = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="CO₂ Evitado (kg)"
    )
    economia_reais = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Economia Estimada (R$)"
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('online', 'Online'),
            ('offline', 'Offline'),
            ('manutencao', 'Manutenção'),
            ('alerta', 'Alerta'),
            ('erro', 'Erro'),
        ],
        default='online'
    )

    class Meta:
        verbose_name = "Leitura da Usina"
        verbose_name_plural = "Leituras das Usinas"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['usina', '-timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.usina.nome} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        from decimal import Decimal
        
        # Calcular CO2 evitado (fator médio: 0.475 kg CO2/kWh no Brasil)
        if self.energia_dia_kwh and not self.co2_evitado_kg:
            self.co2_evitado_kg = self.energia_dia_kwh * Decimal('0.475')
        
        # Calcular economia estimada (tarifa média: R$ 0.80/kWh)
        if self.energia_dia_kwh and not self.economia_reais:
            self.economia_reais = self.energia_dia_kwh * Decimal('0.80')
        
        super().save(*args, **kwargs)


class AlertaUsina(models.Model):
    """Alertas e notificações das usinas"""
    usina = models.ForeignKey(
        UsinaSolar, 
        on_delete=models.CASCADE, 
        related_name='alertas'
    )
    timestamp = models.DateTimeField(default=timezone.now)
    
    tipo = models.CharField(
        max_length=20,
        choices=[
            ('info', 'Informação'),
            ('aviso', 'Aviso'),
            ('alerta', 'Alerta'),
            ('critico', 'Crítico'),
        ]
    )
    categoria = models.CharField(
        max_length=50,
        choices=[
            ('producao', 'Produção'),
            ('temperatura', 'Temperatura'),
            ('tensao', 'Tensão'),
            ('comunicacao', 'Comunicação'),
            ('eficiencia', 'Eficiência'),
            ('manutencao', 'Manutenção'),
            ('outro', 'Outro'),
        ]
    )
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    resolvido = models.BooleanField(default=False)
    resolvido_em = models.DateTimeField(null=True, blank=True)
    observacoes_resolucao = models.TextField(blank=True)

    class Meta:
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.titulo}"


class RelatorioMensal(models.Model):
    """Relatório consolidado mensal da usina"""
    usina = models.ForeignKey(
        UsinaSolar, 
        on_delete=models.CASCADE, 
        related_name='relatorios'
    )
    mes = models.IntegerField(verbose_name="Mês")
    ano = models.IntegerField(verbose_name="Ano")
    
    energia_gerada_total_kwh = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name="Energia Total Gerada (kWh)"
    )
    energia_media_dia_kwh = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Média Diária (kWh)"
    )
    potencia_pico_kw = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Potência Pico (kW)"
    )
    horas_sol_pico = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        verbose_name="Horas de Sol Pico"
    )
    
    co2_evitado_total_kg = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name="CO₂ Total Evitado (kg)"
    )
    economia_total_reais = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name="Economia Total (R$)"
    )
    
    eficiencia_media_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Eficiência Média (%)"
    )
    
    dias_offline = models.IntegerField(default=0, verbose_name="Dias Offline")
    
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Relatório Mensal"
        verbose_name_plural = "Relatórios Mensais"
        ordering = ['-ano', '-mes']
        unique_together = ['usina', 'mes', 'ano']

    def __str__(self):
        return f"{self.usina.nome} - {self.mes:02d}/{self.ano}"


# Importar modelos meteorológicos
from .models_meteorologia import DadosMeteorologicos, AnalisePerformance
