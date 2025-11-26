"""
Script para popular o banco de dados com dados completos das usinas solares
Versão 2 - Com Inversores e Placas Solares
Execute: python populate_solar_data_v2.py
"""

import os
import django
from datetime import datetime, timedelta, date
from decimal import Decimal
import random

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from solar_monitor.models import (
    Inversor, ModeloPlacaSolar, ConfiguracaoPlacasUsina,
    UsinaSolar, LeituraUsina, AlertaUsina
)
from django.utils import timezone


def limpar_dados_antigos():
    """Limpar dados antigos para recriar do zero"""
    print("\nLimpando dados antigos...")
    LeituraUsina.objects.all().delete()
    AlertaUsina.objects.all().delete()
    ConfiguracaoPlacasUsina.objects.all().delete()
    Inversor.objects.all().delete()
    ModeloPlacaSolar.objects.all().delete()
    UsinaSolar.objects.all().delete()
    print("✓ Dados antigos removidos")


def criar_modelos_placas():
    """Criar modelos de placas solares"""
    print("\n1. Criando modelos de placas solares...")
    
    modelos_data = [
        {
            'fabricante': 'Canadian Solar',
            'modelo': 'HiKu6 Mono PERC CS6R-410MS',
            'potencia_pico_wp': Decimal('410'),
            'tensao_circuito_aberto_voc': Decimal('49.6'),
            'corrente_curto_circuito_isc': Decimal('10.57'),
            'tensao_maxima_potencia_vmp': Decimal('41.7'),
            'corrente_maxima_potencia_imp': Decimal('9.84'),
            'eficiencia_percent': Decimal('20.5'),
            'tecnologia': 'perc',
            'coef_temp_potencia_percent': Decimal('-0.350'),
            'comprimento_mm': 2094,
            'largura_mm': 1038,
            'espessura_mm': 35,
            'peso_kg': Decimal('22.5'),
            'numero_celulas': 144,
            'bifacial': False,
        },
        {
            'fabricante': 'JinkoSolar',
            'modelo': 'Tiger Pro 72HC 545W',
            'potencia_pico_wp': Decimal('545'),
            'tensao_circuito_aberto_voc': Decimal('49.95'),
            'corrente_curto_circuito_isc': Decimal('13.96'),
            'tensao_maxima_potencia_vmp': Decimal('41.85'),
            'corrente_maxima_potencia_imp': Decimal('13.02'),
            'eficiencia_percent': Decimal('21.18'),
            'tecnologia': 'perc',
            'coef_temp_potencia_percent': Decimal('-0.350'),
            'comprimento_mm': 2278,
            'largura_mm': 1134,
            'espessura_mm': 35,
            'peso_kg': Decimal('27.5'),
            'numero_celulas': 144,
            'bifacial': True,
            'bifacialidade_percent': Decimal('70.00'),
        },
        {
            'fabricante': 'Trina Solar',
            'modelo': 'Vertex S+ 440W Bifacial',
            'potencia_pico_wp': Decimal('440'),
            'tensao_circuito_aberto_voc': Decimal('50.1'),
            'corrente_curto_circuito_isc': Decimal('11.22'),
            'tensao_maxima_potencia_vmp': Decimal('42.0'),
            'corrente_maxima_potencia_imp': Decimal('10.48'),
            'eficiencia_percent': Decimal('21.4'),
            'tecnologia': 'bifacial',
            'coef_temp_potencia_percent': Decimal('-0.340'),
            'comprimento_mm': 1762,
            'largura_mm': 1134,
            'espessura_mm': 30,
            'peso_kg': Decimal('21.0'),
            'numero_celulas': 144,
            'bifacial': True,
            'bifacialidade_percent': Decimal('75.00'),
        },
    ]
    
    modelos = []
    for data in modelos_data:
        modelo, created = ModeloPlacaSolar.objects.get_or_create(
            fabricante=data['fabricante'],
            modelo=data['modelo'],
            defaults=data
        )
        if created:
            print(f"  ✓ {modelo.fabricante} {modelo.modelo} - {modelo.potencia_pico_wp}Wp")
        modelos.append(modelo)
    
    return modelos


def criar_usinas():
    """Criar usinas solares"""
    print("\n2. Criando usinas solares...")
    
    usinas_data = [
        {
            'nome': 'Usina Solar Lisboa - Matriz',
            'localizacao': 'Recife - PE',
            'capacidade_kwp': Decimal('500.00'),
            'latitude': Decimal('-8.047562'),
            'longitude': Decimal('-34.877001'),
            'data_instalacao': date(2023, 1, 15),
        },
        {
            'nome': 'Usina Solar Lisboa - Filial Norte',
            'localizacao': 'Olinda - PE',
            'capacidade_kwp': Decimal('350.00'),
            'latitude': Decimal('-8.008929'),
            'longitude': Decimal('-34.855350'),
            'data_instalacao': date(2023, 6, 10),
        },
        {
            'nome': 'Usina Solar Lisboa - Filial Sul',
            'localizacao': 'Jaboatão dos Guararapes - PE',
            'capacidade_kwp': Decimal('280.00'),
            'latitude': Decimal('-8.112951'),
            'longitude': Decimal('-35.015198'),
            'data_instalacao': date(2024, 2, 20),
        },
    ]
    
    usinas = []
    for data in usinas_data:
        usina, created = UsinaSolar.objects.get_or_create(
            nome=data['nome'],
            defaults=data
        )
        if created:
            print(f"  ✓ {usina.nome}")
        usinas.append(usina)
    
    return usinas


def criar_inversores(usinas):
    """Criar inversores para as usinas"""
    print("\n3. Criando inversores...")
    
    # Matriz - 2 inversores Fronius
    inv1 = Inversor.objects.create(
        usina=usinas[0],
        fabricante='Fronius',
        modelo='Symo 20.0-3 480',
        numero_serie='29432985-001',
        potencia_nominal_kw=Decimal('20.0'),
        potencia_maxima_dc_kw=Decimal('30.0'),
        tensao_entrada_min_v=Decimal('150'),
        tensao_entrada_max_v=Decimal('1000'),
        tensao_mppt_min_v=Decimal('250'),
        tensao_mppt_max_v=Decimal('800'),
        tensao_saida_v=Decimal('380'),
        corrente_entrada_max_a=Decimal('33'),
        corrente_saida_max_a=Decimal('32'),
        eficiencia_maxima_percent=Decimal('98.1'),
        eficiencia_europeia_percent=Decimal('97.6'),
        numero_mppt=2,
        strings_por_mppt=5,
        tipo_comunicacao='Ethernet, Wi-Fi, Modbus RTU',
        data_instalacao=date(2023, 1, 15),
        anos_garantia=10,
        peso_kg=Decimal('35.0'),
    )
    print(f"  ✓ {inv1.usina.nome}: {inv1.fabricante} {inv1.modelo}")
    
    inv2 = Inversor.objects.create(
        usina=usinas[0],
        fabricante='Fronius',
        modelo='Symo 15.0-3 480',
        numero_serie='29432985-002',
        potencia_nominal_kw=Decimal('15.0'),
        potencia_maxima_dc_kw=Decimal('22.5'),
        tensao_entrada_min_v=Decimal('150'),
        tensao_entrada_max_v=Decimal('1000'),
        tensao_mppt_min_v=Decimal('250'),
        tensao_mppt_max_v=Decimal('800'),
        tensao_saida_v=Decimal('380'),
        corrente_entrada_max_a=Decimal('25'),
        corrente_saida_max_a=Decimal('24'),
        eficiencia_maxima_percent=Decimal('98.0'),
        eficiencia_europeia_percent=Decimal('97.5'),
        numero_mppt=2,
        strings_por_mppt=5,
        tipo_comunicacao='Ethernet, Wi-Fi, Modbus RTU',
        data_instalacao=date(2023, 1, 15),
        anos_garantia=10,
        peso_kg=Decimal('32.0'),
    )
    print(f"  ✓ {inv2.usina.nome}: {inv2.fabricante} {inv2.modelo}")
    
    # Filial Norte - 1 inversor SMA
    inv3 = Inversor.objects.create(
        usina=usinas[1],
        fabricante='SMA',
        modelo='Sunny Tripower 25000TL',
        numero_serie='2190543271',
        potencia_nominal_kw=Decimal('25.0'),
        potencia_maxima_dc_kw=Decimal('37.5'),
        tensao_entrada_min_v=Decimal('150'),
        tensao_entrada_max_v=Decimal('1000'),
        tensao_mppt_min_v=Decimal('265'),
        tensao_mppt_max_v=Decimal('800'),
        tensao_saida_v=Decimal('380'),
        corrente_entrada_max_a=Decimal('66'),
        corrente_saida_max_a=Decimal('40'),
        eficiencia_maxima_percent=Decimal('98.3'),
        eficiencia_europeia_percent=Decimal('98.0'),
        numero_mppt=2,
        strings_por_mppt=6,
        tipo_comunicacao='Ethernet, WLAN, Modbus',
        data_instalacao=date(2023, 6, 10),
        anos_garantia=5,
        peso_kg=Decimal('61.0'),
    )
    print(f"  ✓ {inv3.usina.nome}: {inv3.fabricante} {inv3.modelo}")
    
    # Filial Sul - 1 inversor Huawei
    inv4 = Inversor.objects.create(
        usina=usinas[2],
        fabricante='Huawei',
        modelo='SUN2000-20KTL-M2',
        numero_serie='H20KT210001',
        potencia_nominal_kw=Decimal('20.0'),
        potencia_maxima_dc_kw=Decimal('30.0'),
        tensao_entrada_min_v=Decimal('140'),
        tensao_entrada_max_v=Decimal('1000'),
        tensao_mppt_min_v=Decimal('200'),
        tensao_mppt_max_v=Decimal('850'),
        tensao_saida_v=Decimal('380'),
        corrente_entrada_max_a=Decimal('30'),
        corrente_saida_max_a=Decimal('32'),
        eficiencia_maxima_percent=Decimal('98.6'),
        eficiencia_europeia_percent=Decimal('98.3'),
        numero_mppt=2,
        strings_por_mppt=12,
        tipo_comunicacao='4G, Wi-Fi, Ethernet',
        data_instalacao=date(2024, 2, 20),
        anos_garantia=10,
        peso_kg=Decimal('27.0'),
    )
    print(f"  ✓ {inv4.usina.nome}: {inv4.fabricante} {inv4.modelo}")
    
    return [inv1, inv2, inv3, inv4]


def criar_configuracoes_placas(usinas, modelos_placas, inversores):
    """Criar configurações de placas para cada usina"""
    print("\n4. Configurando placas solares...")
    
    # Matriz - Canadian Solar 410W
    # Vmp = 41.7V, então 18 placas/string = 750.6V (dentro da faixa MPPT 250-800V)
    config1 = ConfiguracaoPlacasUsina.objects.create(
        usina=usinas[0],
        modelo_placa=modelos_placas[0],  # Canadian Solar 410W
        quantidade_placas=1224,  # 68 strings × 18 placas
        quantidade_strings=68,
        placas_por_string=18,
        orientacao_azimutal=Decimal('180.00'),  # Sul
        inclinacao_graus=Decimal('10.00'),
        tipo_instalacao='telhado',
        inversor=inversores[0],  # Fronius 20kW
        mppt_utilizado=1,
        sombreamento_estimado_percent=Decimal('2.00'),
        data_instalacao=date(2023, 1, 15),
    )
    print(f"  ✓ {config1.usina.nome}: {config1.quantidade_placas}x {config1.modelo_placa.potencia_pico_wp}Wp = {config1.potencia_total_kwp}kWp")
    
    # Filial Norte - JinkoSolar 545W Bifacial
    # Vmp = 41.85V, então 18 placas/string = 753.3V (dentro da faixa MPPT 265-800V)
    config2 = ConfiguracaoPlacasUsina.objects.create(
        usina=usinas[1],
        modelo_placa=modelos_placas[1],  # JinkoSolar 545W
        quantidade_placas=648,  # 36 strings × 18 placas
        quantidade_strings=36,
        placas_por_string=18,
        orientacao_azimutal=Decimal('180.00'),
        inclinacao_graus=Decimal('12.00'),
        tipo_instalacao='solo',
        inversor=inversores[2],  # SMA 25kW
        mppt_utilizado=1,
        sombreamento_estimado_percent=Decimal('0.50'),
        data_instalacao=date(2023, 6, 10),
    )
    print(f"  ✓ {config2.usina.nome}: {config2.quantidade_placas}x {config2.modelo_placa.potencia_pico_wp}Wp = {config2.potencia_total_kwp}kWp")
    
    # Filial Sul - Trina Solar 440W Bifacial
    # Vmp = 42.0V, então 18 placas/string = 756V (dentro da faixa MPPT 200-850V)
    config3 = ConfiguracaoPlacasUsina.objects.create(
        usina=usinas[2],
        modelo_placa=modelos_placas[2],  # Trina Solar 440W
        quantidade_placas=648,  # 36 strings × 18 placas
        quantidade_strings=36,
        placas_por_string=18,
        orientacao_azimutal=Decimal('175.00'),
        inclinacao_graus=Decimal('11.00'),
        tipo_instalacao='solo',
        inversor=inversores[3],  # Huawei 20kW
        mppt_utilizado=1,
        sombreamento_estimado_percent=Decimal('1.00'),
        data_instalacao=date(2024, 2, 20),
    )
    print(f"  ✓ {config3.usina.nome}: {config3.quantidade_placas}x {config3.modelo_placa.potencia_pico_wp}Wp = {config3.potencia_total_kwp}kWp")


def criar_leituras_historicas(usina, dias=7):
    """Criar leituras históricas para uma usina"""
    print(f"\n  Criando leituras para {usina.nome}...")
    
    now = timezone.now()
    leituras_criadas = 0
    
    for dia in range(dias):
        data = now - timedelta(days=dia)
        
        # Simular geração solar (6h às 18h)
        for hora in range(6, 19):
            timestamp = data.replace(hour=hora, minute=random.randint(0, 59), second=0)
            
            # Simular curva de geração solar
            hora_pico = 12
            distancia_pico = abs(hora - hora_pico)
            fator_geracao = max(0, 1 - (distancia_pico / 6))
            fator_geracao *= random.uniform(0.7, 1.0)
            
            potencia_max = float(usina.capacidade_kwp) * 0.85
            potencia_atual = potencia_max * fator_geracao
            energia_dia = potencia_max * fator_geracao * (hora - 6 + 0.5)
            
            irradiancia = 1000 * fator_geracao + random.uniform(-50, 50)
            temp_modulo = 25 + (fator_geracao * 20) + random.uniform(-3, 3)
            temp_ambiente = 22 + (fator_geracao * 8) + random.uniform(-2, 2)
            
            tensao = 380 + random.uniform(-10, 10)
            corrente = (potencia_atual * 1000) / (tensao * 1.732) if potencia_atual > 0 else 0
            frequencia = 60 + random.uniform(-0.2, 0.2)
            
            eficiencia = 85 + random.uniform(-5, 5)
            fator_potencia = 0.99 + random.uniform(-0.02, 0.01)
            
            status = 'online'
            if random.random() < 0.05:
                status = 'alerta'
            elif random.random() < 0.02:
                status = 'offline'
                potencia_atual = 0
                energia_dia = 0
            
            LeituraUsina.objects.create(
                usina=usina,
                timestamp=timestamp,
                potencia_atual_kw=Decimal(str(round(potencia_atual, 3))),
                energia_gerada_kwh=Decimal(str(round(energia_dia * 1.5, 3))),
                energia_dia_kwh=Decimal(str(round(energia_dia, 3))),
                irradiancia_w_m2=Decimal(str(round(irradiancia, 2))),
                temperatura_modulo_c=Decimal(str(round(temp_modulo, 2))),
                temperatura_ambiente_c=Decimal(str(round(temp_ambiente, 2))),
                tensao_v=Decimal(str(round(tensao, 2))),
                corrente_a=Decimal(str(round(corrente, 2))),
                frequencia_hz=Decimal(str(round(frequencia, 2))),
                eficiencia_percent=Decimal(str(round(eficiencia, 2))),
                fator_potencia=Decimal(str(round(fator_potencia, 3))),
                status=status
            )
            leituras_criadas += 1
    
    print(f"  ✓ {leituras_criadas} leituras criadas")


def main():
    print("=" * 70)
    print("POPULANDO BANCO DE DADOS - MONITORAMENTO SOLAR V2")
    print("=" * 70)
    
    # Limpar dados antigos
    limpar_dados_antigos()
    
    # Criar modelos de placas
    modelos_placas = criar_modelos_placas()
    
    # Criar usinas
    usinas = criar_usinas()
    
    # Criar inversores
    inversores = criar_inversores(usinas)
    
    # Configurar placas
    criar_configuracoes_placas(usinas, modelos_placas, inversores)
    
    # Criar leituras históricas
    print("\n5. Criando leituras históricas (últimos 7 dias)...")
    for usina in usinas:
        criar_leituras_historicas(usina, dias=7)
    
    # Resumo
    print("\n" + "=" * 70)
    print("RESUMO:")
    print("=" * 70)
    print(f"✓ Usinas criadas: {UsinaSolar.objects.count()}")
    print(f"✓ Inversores criados: {Inversor.objects.count()}")
    print(f"✓ Modelos de placas: {ModeloPlacaSolar.objects.count()}")
    print(f"✓ Configurações de placas: {ConfiguracaoPlacasUsina.objects.count()}")
    print(f"✓ Leituras criadas: {LeituraUsina.objects.count()}")
    
    # Mostrar capacidades
    print("\n" + "=" * 70)
    print("DETALHES DAS USINAS:")
    print("=" * 70)
    for usina in UsinaSolar.objects.all():
        print(f"\n{usina.nome}:")
        print(f"  • Capacidade: {usina.capacidade_kwp} kWp")
        print(f"  • Inversores: {usina.quantidade_inversores} ({usina.potencia_total_inversores_kw}kW)")
        print(f"  • Fator DC/AC: {usina.fator_dimensionamento:.2f}")
        print(f"  • Placas: {usina.quantidade_total_placas} unidades")
        print(f"  • Área: {usina.area_total_m2:.2f} m²")
    
    print("\n✓ Dados populados com sucesso!")
    print("\nAcesse o dashboard em: http://localhost:8000/solar/")
    print("=" * 70)


if __name__ == '__main__':
    main()
