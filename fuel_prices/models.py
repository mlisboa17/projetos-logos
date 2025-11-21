"""
╔══════════════════════════════════════════════════════════════════╗
║                    MODELS - FUEL_PRICES APP                      ║
║              Sistema de Monitoramento de Preços de Combustível   ║
╚══════════════════════════════════════════════════════════════════╝

📚 O QUE É ESTE ARQUIVO:
------------------------
Define os modelos de dados para controle de preços de combustível:

  1. 🛢️ Fuel: Tipos de combustível (Gasolina, Diesel, Etanol, GNV)
  2. 🏭 Supplier: Fornecedores/Distribuidoras (Vibra, Ipiranga, Raízen)
  3. 💰 PurchasePrice: Compras REAIS com nota fiscal
  4. 🌐 ScrapedPrice: Preços coletados (ALERTA, não é compra)
  5. 🔔 PriceAlert: Alertas inteligentes (divergências, oportunidades)
  6. 🔄 ScrapingLog: Log de execuções do scraper

🔧 COMO FUNCIONA:
-----------------
1. Você COMPRA combustível → Registra em PurchasePrice (manual)
2. Scraper coleta preços da web → Salva em ScrapedPrice (automático)
3. Sistema compara suas compras vs preços scraped
4. Detecta divergências entre seus postos
5. Cria alertas: "Posto X pagou mais caro!" ou "Oportunidade!"
6. Gestor visualiza dashboard com alertas

🎯 EXEMPLOS DE ALERTAS:
-----------------------
- "Posto Norte pagou R$ 0,05 a mais que Posto Centro!"
- "Vibra oferece R$ 4,48 (você pagou R$ 4,55 ontem)"
- "Prazo de 60 dias disponível (você está com 30 dias)"
- "Pagamento antecipado: desconto de 2% disponível"

📚 DOCUMENTAÇÃO:
----------------
Django Models: https://docs.djangoproject.com/en/5.2/topics/db/models/
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import timedelta


# ============================================================
# 📋 ENUMERAÇÕES (Choices)
# ============================================================

class FuelType(models.TextChoices):
    """
    Tipos de combustível comercializados
    
    Baseado em produtos comuns em postos brasileiros
    """
    GASOLINE_COMMON = 'gasoline_common', 'Gasolina Comum'           # ⛽ Mais vendido
    GASOLINE_PREMIUM = 'gasoline_premium', 'Gasolina Aditivada'     # ⛽ Premium
    ETHANOL = 'ethanol', 'Etanol (Álcool)'                          # 🌽 Hidratado
    DIESEL_S10 = 'diesel_s10', 'Diesel S10'                         # 🚛 Baixo enxofre
    DIESEL_S500 = 'diesel_s500', 'Diesel S500'                      # 🚛 Comum
    GNV = 'gnv', 'GNV (Gás Natural Veicular)'                       # 💨 Gás


class FreightMode(models.TextChoices):
    """
    Modalidade de frete na compra
    
    CIF = Distribuidora paga frete (Cost, Insurance and Freight)
    FOB = Posto paga frete (Free On Board)
    """
    CIF = 'CIF', 'CIF (Vendedor paga frete)'      # Distribuidora entrega
    FOB = 'FOB', 'FOB (Comprador paga frete)'     # Posto busca/paga


class PaymentTermType(models.TextChoices):
    """
    Tipos de prazo de pagamento
    
    ANTECIPADO = Pagamento à vista (com desconto)
    NORMAL = Prazo padrão (7, 15, 30, 60, 90 dias)
    """
    ANTECIPADO = 'antecipado', 'Antecipado (À Vista)'  # Com desconto
    PRAZO = 'prazo', 'A Prazo'                         # Parcelado


class PriceSource(models.TextChoices):
    """
    Origem/fonte do preço
    """
    VIBRA_PORTAL = 'vibra_portal', 'Portal Vibra Energia'    # Site Vibra
    ANP = 'anp', 'ANP (Dados Oficiais)'                      # Governo
    MANUAL = 'manual', 'Entrada Manual'                       # Digitado
    IPIRANGA = 'ipiranga', 'Portal Ipiranga'                 # Site Ipiranga
    RAIZEN = 'raizen', 'Portal Raízen'                       # Site Raízen


class AlertType(models.TextChoices):
    """
    Tipos de alertas gerados pelo sistema
    """
    # Divergência entre seus postos
    INTERNAL_DIVERGENCE = 'internal_divergence', '⚠️ Divergência Entre Postos'
    
    # Oportunidades detectadas
    BETTER_PRICE = 'better_price', '💡 Preço Melhor Disponível'
    BETTER_TERMS = 'better_terms', '📅 Condições Melhores (Prazo/Frete)'
    EARLY_PAYMENT_DISCOUNT = 'early_payment', '💰 Desconto Antecipado Disponível'
    
    # Variações de mercado
    PRICE_INCREASE = 'price_increase', '📈 Aumento de Preço Detectado'
    PRICE_DECREASE = 'price_decrease', '📉 Redução de Preço Detectada'


class AlertPriority(models.TextChoices):
    """
    Prioridade do alerta
    """
    HIGH = 'high', '🔴 Alta'        # Diferença > R$ 0,10/L
    MEDIUM = 'medium', '🟡 Média'   # Diferença R$ 0,05-0,10/L
    LOW = 'low', '🟢 Baixa'         # Diferença < R$ 0,05/L


# ============================================================
# 🛢️ MODEL: FUEL (Combustível)
# ============================================================

class Fuel(models.Model):
    """
    Tipo de combustível comercializado
    
    ╔══════════════════════════════════════════════════════════╗
    ║  EXEMPLOS:                                               ║
    ║  - Gasolina Comum                                        ║
    ║  - Diesel S10                                            ║
    ║  - Etanol                                                ║
    ║  - GNV                                                   ║
    ╚══════════════════════════════════════════════════════════╝
    
    Cada combustível tem código ANP oficial e características próprias
    """
    
    # ──────────────────────────────────────────────────────────
    # 📝 DADOS BÁSICOS
    # ──────────────────────────────────────────────────────────
    
    name = models.CharField(
        'Nome',
        max_length=100,
        unique=True,
        help_text='Nome do combustível (ex: Gasolina Comum)'
    )
    
    code = models.CharField(
        'Código Interno',
        max_length=10,
        unique=True,
        help_text='Código interno (ex: GC, DS10, ET)'
    )
    
    anp_code = models.CharField(
        'Código ANP',
        max_length=20,
        blank=True,
        help_text='Código oficial da ANP (ex: 320101 para Gasolina C)'
    )
    
    fuel_type = models.CharField(
        'Tipo',
        max_length=30,
        choices=FuelType.choices,
        help_text='Categoria do combustível'
    )
    
    # ──────────────────────────────────────────────────────────
    # 📊 CARACTERÍSTICAS TÉCNICAS
    # ──────────────────────────────────────────────────────────
    
    unit = models.CharField(
        'Unidade',
        max_length=10,
        default='litro',
        help_text='Unidade de medida (litro, m³, kg)'
    )
    
    density = models.DecimalField(
        'Densidade (kg/L)',
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        help_text='Densidade aproximada (ex: 0.750 para gasolina)'
    )
    
    # ──────────────────────────────────────────────────────────
    # 📝 INFORMAÇÕES ADICIONAIS
    # ──────────────────────────────────────────────────────────
    
    description = models.TextField(
        'Descrição',
        blank=True,
        help_text='Informações técnicas e características'
    )
    
    is_active = models.BooleanField(
        'Ativo',
        default=True,
        help_text='Se está disponível para comercialização'
    )
    
    # ──────────────────────────────────────────────────────────
    # 🗂️ METADATA
    # ──────────────────────────────────────────────────────────
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Combustível'
        verbose_name_plural = 'Combustíveis'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


# ============================================================
# 🏭 MODEL: SUPPLIER (Fornecedor/Distribuidora)
# ============================================================

class Supplier(models.Model):
    """
    Distribuidora de combustível
    
    ╔══════════════════════════════════════════════════════════╗
    ║  EXEMPLOS:                                               ║
    ║  - Vibra Energia                                         ║
    ║  - Ipiranga                                              ║
    ║  - Raízen                                                ║
    ║  - Ale Combustíveis                                      ║
    ╚══════════════════════════════════════════════════════════╝
    """
    
    # ──────────────────────────────────────────────────────────
    # 📝 DADOS BÁSICOS
    # ──────────────────────────────────────────────────────────
    
    name = models.CharField(
        'Razão Social',
        max_length=200,
        help_text='Nome oficial da empresa'
    )
    
    brand = models.CharField(
        'Marca/Bandeira',
        max_length=100,
        help_text='Nome comercial (ex: Vibra, Shell, Ipiranga)'
    )
    
    cnpj = models.CharField(
        'CNPJ',
        max_length=18,
        unique=True,
        help_text='CNPJ da distribuidora'
    )
    
    # ──────────────────────────────────────────────────────────
    # 📞 CONTATO
    # ──────────────────────────────────────────────────────────
    
    contact_name = models.CharField(
        'Nome do Contato',
        max_length=200,
        blank=True,
        help_text='Representante comercial'
    )
    
    contact_phone = models.CharField(
        'Telefone',
        max_length=20,
        blank=True
    )
    
    contact_email = models.EmailField(
        'Email',
        blank=True
    )
    
    # ──────────────────────────────────────────────────────────
    # 🌐 PORTAL WEB
    # ──────────────────────────────────────────────────────────
    
    portal_url = models.URLField(
        'URL do Portal',
        blank=True,
        help_text='URL do sistema web da distribuidora'
    )
    
    has_web_scraping = models.BooleanField(
        'Possui Scraping',
        default=False,
        help_text='Se temos scraper configurado para este fornecedor'
    )
    
    # ──────────────────────────────────────────────────────────
    # 📝 OBSERVAÇÕES
    # ──────────────────────────────────────────────────────────
    
    notes = models.TextField(
        'Observações',
        blank=True,
        help_text='Condições especiais, histórico de negociações'
    )
    
    is_active = models.BooleanField(
        'Ativo',
        default=True
    )
    
    # ──────────────────────────────────────────────────────────
    # 🗂️ METADATA
    # ──────────────────────────────────────────────────────────
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'
        ordering = ['brand']
    
    def __str__(self):
        return f"{self.brand} ({self.cnpj})"


# ============================================================
# 💰 MODEL: PURCHASE PRICE (Compra Real)
# ============================================================

class PurchasePrice(models.Model):
    """
    Registro de compra REAL de combustível
    
    ╔══════════════════════════════════════════════════════════╗
    ║  O QUE É:                                                ║
    ║  Quando você REALMENTE compra combustível                ║
    ║  Baseado em NOTA FISCAL real                             ║
    ║  Digitado manualmente pela equipe                        ║
    ║                                                          ║
    ║  IMPORTANTE:                                             ║
    ║  NÃO confundir com ScrapedPrice (que é apenas alerta)    ║
    ╚══════════════════════════════════════════════════════════╝
    
    Exemplo:
    --------
    Posto Centro comprou 10.000L de Gasolina Comum
    Da Vibra Energia por R$ 4,50/L
    Frete FOB: R$ 500 (posto pagou)
    Custo final: R$ 4,55/L
    Prazo: 30 dias
    NF: 12345
    """
    
    # ──────────────────────────────────────────────────────────
    # 🔗 RELACIONAMENTOS
    # ──────────────────────────────────────────────────────────
    
    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.CASCADE,
        related_name='fuel_purchases',
        help_text='Organização que fez a compra'
    )
    
    store = models.ForeignKey(
        'erp_hub.Store',
        on_delete=models.CASCADE,
        related_name='fuel_purchases',
        help_text='Qual posto/loja comprou este combustível'
    )
    
    fuel = models.ForeignKey(
        Fuel,
        on_delete=models.PROTECT,
        related_name='purchases',
        help_text='Tipo de combustível comprado'
    )
    
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='sales',
        help_text='Distribuidora que vendeu'
    )
    
    # ──────────────────────────────────────────────────────────
    # 💰 PREÇO E VOLUME
    # ──────────────────────────────────────────────────────────
    
    unit_price = models.DecimalField(
        'Preço Unitário (Base)',
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        help_text='Preço por litro SEM frete (ex: R$ 4,500)'
    )
    
    volume_liters = models.DecimalField(
        'Volume (Litros)',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Quantidade de litros comprada (ex: 10000.00)'
    )
    
    total_value = models.DecimalField(
        'Valor Total da NF',
        max_digits=12,
        decimal_places=2,
        help_text='Valor total da nota fiscal (unit_price * volume + frete)'
    )
    
    # ──────────────────────────────────────────────────────────
    # 🚚 FRETE
    # ──────────────────────────────────────────────────────────
    
    freight_mode = models.CharField(
        'Modalidade de Frete',
        max_length=3,
        choices=FreightMode.choices,
        default=FreightMode.CIF,
        help_text='CIF = Vendedor paga | FOB = Comprador paga'
    )
    
    freight_value = models.DecimalField(
        'Valor do Frete',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Custo do frete em reais (R$ 0,00 se CIF)'
    )
    
    freight_per_liter = models.DecimalField(
        'Frete por Litro',
        max_digits=6,
        decimal_places=3,
        default=Decimal('0.000'),
        help_text='Calculado: freight_value / volume_liters'
    )
    
    # ──────────────────────────────────────────────────────────
    # 💵 CUSTO FINAL
    # ──────────────────────────────────────────────────────────
    
    final_unit_cost = models.DecimalField(
        'Custo Final por Litro',
        max_digits=10,
        decimal_places=3,
        help_text='unit_price + freight_per_liter (CUSTO REAL)'
    )
    
    # ──────────────────────────────────────────────────────────
    # 📅 PAGAMENTO
    # ──────────────────────────────────────────────────────────
    
    payment_term_type = models.CharField(
        'Tipo de Prazo',
        max_length=20,
        choices=PaymentTermType.choices,
        default=PaymentTermType.PRAZO,
        help_text='Antecipado (à vista) ou A Prazo'
    )
    
    payment_term_days = models.IntegerField(
        'Prazo (Dias)',
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(365)],
        help_text='0 = à vista | 7, 15, 30, 60, 90 dias'
    )
    
    early_payment_discount_percent = models.DecimalField(
        'Desconto Antecipado (%)',
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text='% de desconto se pagar à vista (ex: 2.00 = 2%)'
    )
    
    payment_due_date = models.DateField(
        'Vencimento',
        help_text='invoice_date + payment_term_days'
    )
    
    # ──────────────────────────────────────────────────────────
    # 📄 NOTA FISCAL
    # ──────────────────────────────────────────────────────────
    
    invoice_number = models.CharField(
        'Número da NF',
        max_length=50,
        help_text='Número da nota fiscal'
    )
    
    invoice_date = models.DateField(
        'Data da NF',
        help_text='Data de emissão da nota fiscal'
    )
    
    invoice_file = models.FileField(
        'Arquivo da NF',
        upload_to='fuel_invoices/%Y/%m/',
        null=True,
        blank=True,
        help_text='Upload do PDF da nota fiscal (opcional)'
    )
    
    # ──────────────────────────────────────────────────────────
    # 📝 OBSERVAÇÕES
    # ──────────────────────────────────────────────────────────
    
    notes = models.TextField(
        'Observações',
        blank=True,
        help_text='Negociações especiais, condições extras'
    )
    
    # ──────────────────────────────────────────────────────────
    # 🗂️ METADATA
    # ──────────────────────────────────────────────────────────
    
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='fuel_purchases_created',
        help_text='Usuário que registrou esta compra'
    )
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Compra de Combustível'
        verbose_name_plural = 'Compras de Combustível'
        ordering = ['-invoice_date', '-created_at']
        
        # Índices para queries rápidas
        indexes = [
            models.Index(fields=['store', 'fuel', '-invoice_date']),
            models.Index(fields=['supplier', '-invoice_date']),
            models.Index(fields=['invoice_date']),
        ]
    
    def __str__(self):
        return f"{self.store.name} - {self.fuel.name} - R$ {self.final_unit_cost:.3f}/L - {self.invoice_date.strftime('%d/%m/%Y')}"
    
    def save(self, *args, **kwargs):
        """
        Calcula campos automáticos antes de salvar
        
        O que faz:
        ----------
        1. Calcula frete por litro (freight_value / volume_liters)
        2. Calcula custo final (unit_price + freight_per_liter)
        3. Calcula vencimento (invoice_date + payment_term_days)
        """
        # Calcular frete por litro
        if self.freight_value and self.volume_liters:
            self.freight_per_liter = self.freight_value / self.volume_liters
        else:
            self.freight_per_liter = Decimal('0.000')
        
        # Calcular custo final
        self.final_unit_cost = self.unit_price + self.freight_per_liter
        
        # Calcular vencimento
        if self.invoice_date and self.payment_term_days is not None:
            self.payment_due_date = self.invoice_date + timedelta(days=self.payment_term_days)
        
        super().save(*args, **kwargs)
    
    @property
    def price_with_early_discount(self):
        """
        Calcula preço se pagar antecipado
        
        Returns:
        --------
        Decimal: Preço final com desconto antecipado aplicado
        
        Exemplo:
        --------
        Preço normal: R$ 4,550
        Desconto antecipado: 2%
        Preço à vista: R$ 4,459
        """
        if self.early_payment_discount_percent > 0:
            discount_multiplier = (100 - self.early_payment_discount_percent) / 100
            return self.final_unit_cost * discount_multiplier
        return self.final_unit_cost
    
    @property
    def savings_with_early_payment(self):
        """
        Calcula economia total se pagar antecipado
        
        Returns:
        --------
        Decimal: Valor em reais economizado
        """
        if self.early_payment_discount_percent > 0:
            return (self.final_unit_cost - self.price_with_early_discount) * self.volume_liters
        return Decimal('0.00')


# ============================================================
# 🌐 MODEL: SCRAPED PRICE (Preço Coletado)
# ============================================================

class ScrapedPrice(models.Model):
    """
    Preço coletado de sites (ALERTA, NÃO É COMPRA)
    
    ╔══════════════════════════════════════════════════════════╗
    ║  IMPORTANTE:                                             ║
    ║  Coletar preço ≠ Comprar combustível                     ║
    ║                                                          ║
    ║  Este modelo serve para:                                 ║
    ║  ✅ Monitorar preços de referência                       ║
    ║  ✅ Gerar alertas de oportunidade                        ║
    ║  ✅ Comparar com suas compras reais                      ║
    ║  ❌ NÃO representa compra efetivada                      ║
    ╚══════════════════════════════════════════════════════════╝
    
    Exemplo:
    --------
    Scraper acessou Portal Vibra e viu:
    - Posto Norte: Diesel S10 por R$ 4,48 (prazo 30 dias, CIF)
    - Posto Sul: Diesel S10 por R$ 4,52 (prazo 60 dias, FOB)
    
    Se você comprou por R$ 4,60, sistema alerta: "Oportunidade!"
    """
    
    # ──────────────────────────────────────────────────────────
    # 🔗 RELACIONAMENTOS
    # ──────────────────────────────────────────────────────────
    
    store = models.ForeignKey(
        'erp_hub.Store',
        on_delete=models.CASCADE,
        related_name='scraped_prices',
        help_text='Para qual posto este preço foi coletado'
    )
    
    fuel = models.ForeignKey(
        Fuel,
        on_delete=models.CASCADE,
        related_name='scraped_prices',
        help_text='Tipo de combustível'
    )
    
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='scraped_prices',
        help_text='Distribuidora que oferece este preço'
    )
    
    # ──────────────────────────────────────────────────────────
    # 💰 PREÇO
    # ──────────────────────────────────────────────────────────
    
    unit_price = models.DecimalField(
        'Preço Unitário',
        max_digits=10,
        decimal_places=3,
        help_text='Preço por litro coletado do site'
    )
    
    # ──────────────────────────────────────────────────────────
    # 🚚 FRETE (se disponível no site)
    # ──────────────────────────────────────────────────────────
    
    freight_mode = models.CharField(
        'Modalidade de Frete',
        max_length=3,
        choices=FreightMode.choices,
        null=True,
        blank=True,
        help_text='CIF ou FOB (se o site informar)'
    )
    
    freight_included = models.BooleanField(
        'Frete Incluído',
        default=True,
        help_text='Se o preço já inclui frete (CIF)'
    )
    
    # ──────────────────────────────────────────────────────────
    # 📅 PAGAMENTO (se disponível no site)
    # ──────────────────────────────────────────────────────────
    
    payment_term_days = models.IntegerField(
        'Prazo (Dias)',
        null=True,
        blank=True,
        help_text='Prazo de pagamento (se o site informar)'
    )
    
    # ──────────────────────────────────────────────────────────
    # 🌐 ORIGEM
    # ──────────────────────────────────────────────────────────
    
    source = models.CharField(
        'Fonte',
        max_length=30,
        choices=PriceSource.choices,
        help_text='De onde veio este preço'
    )
    
    source_url = models.URLField(
        'URL de Origem',
        blank=True,
        help_text='Página onde foi coletado'
    )
    
    scraped_at = models.DateTimeField(
        'Coletado em',
        help_text='Data/hora da coleta'
    )
    
    # ──────────────────────────────────────────────────────────
    # 📝 DADOS BRUTOS
    # ──────────────────────────────────────────────────────────
    
    raw_data = models.JSONField(
        'Dados Brutos',
        null=True,
        blank=True,
        help_text='JSON completo coletado do site (para debug)'
    )
    
    # ──────────────────────────────────────────────────────────
    # ✅ VALIDAÇÃO
    # ──────────────────────────────────────────────────────────
    
    is_valid = models.BooleanField(
        'Válido',
        default=True,
        help_text='Se consideramos este preço confiável'
    )
    
    validation_notes = models.TextField(
        'Notas de Validação',
        blank=True,
        help_text='Por que marcamos como inválido (se aplicável)'
    )
    
    # ──────────────────────────────────────────────────────────
    # 🗂️ METADATA
    # ──────────────────────────────────────────────────────────
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Preço Coletado (Scraping)'
        verbose_name_plural = 'Preços Coletados (Scraping)'
        ordering = ['-scraped_at']
        
        indexes = [
            models.Index(fields=['store', 'fuel', '-scraped_at']),
            models.Index(fields=['supplier', '-scraped_at']),
            models.Index(fields=['-scraped_at']),
        ]
    
    def __str__(self):
        return f"{self.store.name} - {self.fuel.name} - R$ {self.unit_price:.3f}/L ({self.scraped_at.strftime('%d/%m/%Y %H:%M')})"


# ============================================================
# 🔔 MODEL: PRICE ALERT (Alerta de Preço)
# ============================================================

class PriceAlert(models.Model):
    """
    Alerta inteligente de oportunidade ou divergência
    
    ╔══════════════════════════════════════════════════════════╗
    ║  TIPOS DE ALERTAS:                                       ║
    ║                                                          ║
    ║  1️⃣ Divergência Interna:                                 ║
    ║     "Posto A pagou R$ 0,10 mais caro que Posto B"        ║
    ║     (mesmo produto, fornecedor e condições)              ║
    ║                                                          ║
    ║  2️⃣ Oportunidade de Preço:                               ║
    ║     "Site mostra R$ 4,48 (você pagou R$ 4,60)"           ║
    ║                                                          ║
    ║  3️⃣ Melhores Condições:                                  ║
    ║     "Prazo 60 dias disponível (você está com 30)"        ║
    ║     "Frete CIF disponível (você paga FOB)"               ║
    ║                                                          ║
    ║  4️⃣ Desconto Antecipado:                                 ║
    ║     "Pagamento à vista: desconto de 2%"                  ║
    ╚══════════════════════════════════════════════════════════╝
    """
    
    # ──────────────────────────────────────────────────────────
    # 🔗 RELACIONAMENTOS
    # ──────────────────────────────────────────────────────────
    
    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.CASCADE,
        related_name='fuel_alerts',
        help_text='Organização que recebe o alerta'
    )
    
    # Links opcionais para compras e preços scraped
    purchase_price = models.ForeignKey(
        PurchasePrice,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts',
        help_text='Compra que gerou o alerta (se aplicável)'
    )
    
    scraped_price = models.ForeignKey(
        ScrapedPrice,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts',
        help_text='Preço coletado que gerou o alerta (se aplicável)'
    )
    
    # Comparação entre duas compras (para divergência interna)
    compared_purchase = models.ForeignKey(
        PurchasePrice,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='comparison_alerts',
        help_text='Segunda compra para comparação (divergência interna)'
    )
    
    # ──────────────────────────────────────────────────────────
    # 🏷️ TIPO E PRIORIDADE
    # ──────────────────────────────────────────────────────────
    
    alert_type = models.CharField(
        'Tipo de Alerta',
        max_length=30,
        choices=AlertType.choices,
        help_text='Categoria do alerta'
    )
    
    priority = models.CharField(
        'Prioridade',
        max_length=10,
        choices=AlertPriority.choices,
        default=AlertPriority.MEDIUM,
        help_text='Alta/Média/Baixa'
    )
    
    # ──────────────────────────────────────────────────────────
    # 📊 VALORES
    # ──────────────────────────────────────────────────────────
    
    current_price = models.DecimalField(
        'Preço Atual',
        max_digits=10,
        decimal_places=3,
        help_text='Preço que você está pagando'
    )
    
    better_price = models.DecimalField(
        'Preço Melhor',
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text='Preço melhor disponível (se aplicável)'
    )
    
    price_difference = models.DecimalField(
        'Diferença (R$/L)',
        max_digits=8,
        decimal_places=3,
        help_text='Quanto você está pagando a mais'
    )
    
    potential_savings = models.DecimalField(
        'Economia Potencial (R$)',
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Quanto economizaria (baseado em volume médio)'
    )
    
    # ──────────────────────────────────────────────────────────
    # 📝 MENSAGEM
    # ──────────────────────────────────────────────────────────
    
    title = models.CharField(
        'Título',
        max_length=200,
        help_text='Título curto do alerta'
    )
    
    message = models.TextField(
        'Mensagem',
        help_text='Descrição completa do alerta'
    )
    
    # ──────────────────────────────────────────────────────────
    # ✅ STATUS
    # ──────────────────────────────────────────────────────────
    
    is_read = models.BooleanField(
        'Lido',
        default=False,
        help_text='Se o gestor já visualizou'
    )
    
    read_at = models.DateTimeField(
        'Lido em',
        null=True,
        blank=True
    )
    
    read_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fuel_alerts_read',
        help_text='Usuário que leu o alerta'
    )
    
    is_dismissed = models.BooleanField(
        'Dispensado',
        default=False,
        help_text='Se foi descartado/ignorado'
    )
    
    dismissed_reason = models.TextField(
        'Motivo da Dispensa',
        blank=True,
        help_text='Por que foi ignorado'
    )
    
    # ──────────────────────────────────────────────────────────
    # 🗂️ METADATA
    # ──────────────────────────────────────────────────────────
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    expires_at = models.DateTimeField(
        'Expira em',
        null=True,
        blank=True,
        help_text='Após esta data, alerta perde relevância'
    )
    
    class Meta:
        verbose_name = 'Alerta de Preço'
        verbose_name_plural = 'Alertas de Preço'
        ordering = ['-created_at']
        
        indexes = [
            models.Index(fields=['organization', '-created_at']),
            models.Index(fields=['is_read', '-created_at']),
            models.Index(fields=['priority', '-created_at']),
        ]
    
    def __str__(self):
        status = "✅" if self.is_read else "🔔"
        return f"{status} {self.title} ({self.get_priority_display()})"
    
    def mark_as_read(self, user):
        """
        Marca alerta como lido
        
        Args:
        -----
        user: Usuário que está lendo
        """
        self.is_read = True
        self.read_at = timezone.now()
        self.read_by = user
        self.save(update_fields=['is_read', 'read_at', 'read_by'])


# ============================================================
# 🔄 MODEL: SCRAPING LOG (Log de Execução)
# ============================================================

class ScrapingLog(models.Model):
    """
    Log de execução do scraper
    
    ╔══════════════════════════════════════════════════════════╗
    ║  PARA QUE SERVE:                                         ║
    ║  - Rastrear execuções do scraper                         ║
    ║  - Debugar erros                                         ║
    ║  - Métricas de performance                               ║
    ║  - Auditar coletas                                       ║
    ╚══════════════════════════════════════════════════════════╝
    """
    
    # ──────────────────────────────────────────────────────────
    # 🌐 ORIGEM
    # ──────────────────────────────────────────────────────────
    
    source = models.CharField(
        'Fonte',
        max_length=30,
        choices=PriceSource.choices,
        help_text='Qual site foi acessado'
    )
    
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='scraping_logs',
        help_text='Fornecedor relacionado'
    )
    
    # ──────────────────────────────────────────────────────────
    # ⏱️ TEMPO
    # ──────────────────────────────────────────────────────────
    
    started_at = models.DateTimeField(
        'Iniciado em',
        help_text='Quando começou a execução'
    )
    
    finished_at = models.DateTimeField(
        'Finalizado em',
        null=True,
        blank=True,
        help_text='Quando terminou (NULL se ainda rodando)'
    )
    
    duration_seconds = models.IntegerField(
        'Duração (s)',
        null=True,
        blank=True,
        help_text='Tempo total de execução'
    )
    
    # ──────────────────────────────────────────────────────────
    # ✅ RESULTADO
    # ──────────────────────────────────────────────────────────
    
    status = models.CharField(
        'Status',
        max_length=20,
        choices=[
            ('running', '🔄 Executando'),
            ('success', '✅ Sucesso'),
            ('partial', '⚠️ Parcial'),
            ('failed', '❌ Falhou'),
        ],
        default='running'
    )
    
    prices_collected = models.IntegerField(
        'Preços Coletados',
        default=0,
        help_text='Quantos preços foram salvos'
    )
    
    errors_count = models.IntegerField(
        'Erros',
        default=0,
        help_text='Quantidade de erros encontrados'
    )
    
    # ──────────────────────────────────────────────────────────
    # 📝 DETALHES
    # ──────────────────────────────────────────────────────────
    
    error_message = models.TextField(
        'Mensagem de Erro',
        blank=True,
        help_text='Descrição do erro (se houver)'
    )
    
    log_details = models.JSONField(
        'Detalhes do Log',
        null=True,
        blank=True,
        help_text='Informações técnicas da execução'
    )
    
    # ──────────────────────────────────────────────────────────
    # 🗂️ METADATA
    # ──────────────────────────────────────────────────────────
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Log de Scraping'
        verbose_name_plural = 'Logs de Scraping'
        ordering = ['-started_at']
    
    def __str__(self):
        status_icon = {
            'running': '🔄',
            'success': '✅',
            'partial': '⚠️',
            'failed': '❌',
        }.get(self.status, '❓')
        
        return f"{status_icon} {self.source} - {self.started_at.strftime('%d/%m/%Y %H:%M')} ({self.prices_collected} preços)"
    
    def finish(self, status, prices_count=0, error_message=''):
        """
        Finaliza o log de scraping
        
        Args:
        -----
        status: 'success', 'partial' ou 'failed'
        prices_count: Quantidade de preços coletados
        error_message: Mensagem de erro (se houver)
        """
        self.finished_at = timezone.now()
        self.duration_seconds = int((self.finished_at - self.started_at).total_seconds())
        self.status = status
        self.prices_collected = prices_count
        self.error_message = error_message
        self.save()


# ============================================================
# 🏢 POSTO (Vibra)
# ============================================================

class PostoVibra(models.Model):
    """
    Representa um posto do Grupo Lisboa cadastrado na Vibra
    
    Armazena informações dos 11 postos para organizar os preços
    """
    codigo_vibra = models.CharField('Código Vibra', max_length=20, unique=True)
    razao_social = models.CharField('Razão Social', max_length=200)
    nome_fantasia = models.CharField('Nome Fantasia', max_length=100)
    cnpj = models.CharField('CNPJ', max_length=18, unique=True)
    ativo = models.BooleanField('Ativo', default=True)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Posto Vibra'
        verbose_name_plural = 'Postos Vibra'
        ordering = ['nome_fantasia']
    
    def __str__(self):
        return f"{self.nome_fantasia} ({self.codigo_vibra})"


# ============================================================
# 💰 PREÇO VIBRA
# ============================================================

class PrecoVibra(models.Model):
    """
    Preços de combustíveis coletados do portal Vibra
    
    Armazena histórico de preços por posto e produto
    """
    posto = models.ForeignKey(PostoVibra, on_delete=models.CASCADE, related_name='precos')
    produto_nome = models.CharField('Nome do Produto', max_length=200)
    produto_codigo = models.CharField('Código do Produto', max_length=50)
    
    preco = models.DecimalField('Preço', max_digits=10, decimal_places=4)
    prazo_pagamento = models.CharField('Prazo de Pagamento', max_length=50, blank=True)
    base_distribuicao = models.CharField('Base de Distribuição', max_length=100, blank=True)
    modalidade = models.CharField('Modalidade', max_length=50, blank=True)  # FOB, CIF
    
    data_coleta = models.DateTimeField('Data da Coleta')
    disponivel = models.BooleanField('Disponível', default=True)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Preço Vibra'
        verbose_name_plural = 'Preços Vibra'
        ordering = ['-data_coleta', 'produto_nome', 'posto']
        indexes = [
            models.Index(fields=['-data_coleta', 'produto_nome']),
            models.Index(fields=['posto', '-data_coleta']),
        ]
    
    def __str__(self):
        return f"{self.produto_nome} - {self.posto.nome_fantasia} - R$ {self.preco} ({self.data_coleta.strftime('%d/%m/%Y %H:%M')})"
