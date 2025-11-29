"""
Script para popular o banco de dados com dados de teste das usinas solares
Execute: python populate_solar_data.py
"""

import os
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from solar_monitor.models import UsinaSolar, LeituraUsina, AlertaUsina
from django.utils import timezone


def criar_usinas():
    """Criar usinas solares do Grupo Lisboa"""
    usinas_data = [
        {
            'nome': 'Usina Solar Lisboa - Matriz',
            'localizacao': 'Recife - PE',
            'capacidade_kwp': Decimal('500.00'),
            'latitude': Decimal('-8.047562'),
            'longitude': Decimal('-34.877001'),
            'data_instalacao': datetime(2023, 1, 15).date(),
            'inversor_marca': 'Fronius',
            'inversor_modelo': 'Symo 20.0-3 480',
        },
        {
            'nome': 'Usina Solar Lisboa - Filial Norte',
            'localizacao': 'Olinda - PE',
            'capacidade_kwp': Decimal('350.00'),
            'latitude': Decimal('-8.008929'),
            'longitude': Decimal('-34.855350'),
            'data_instalacao': datetime(2023, 6, 10).date(),
            'inversor_marca': 'SMA',
            'inversor_modelo': 'Sunny Tripower 25000TL',
        },
        {
            'nome': 'Usina Solar Lisboa - Filial Sul',
            'localizacao': 'Jaboatão dos Guararapes - PE',
            'capacidade_kwp': Decimal('280.00'),
            'latitude': Decimal('-8.112951'),
            'longitude': Decimal('-35.015198'),
            'data_instalacao': datetime(2024, 2, 20).date(),
            'inversor_marca': 'Huawei',
            'inversor_modelo': 'SUN2000-33KTL-A',
        },
    ]
    
    usinas = []
    for data in usinas_data:
        usina, created = UsinaSolar.objects.get_or_create(
            nome=data['nome'],
            defaults=data
        )
        if created:
            print(f"✓ Criada: {usina.nome}")
        else:
            print(f"○ Já existe: {usina.nome}")
        usinas.append(usina)
    
    return usinas


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
            
            # Simular curva de geração solar (maior ao meio-dia)
            hora_pico = 12
            distancia_pico = abs(hora - hora_pico)
            fator_geracao = max(0, 1 - (distancia_pico / 6))
            
            # Adicionar variação aleatória
            fator_geracao *= random.uniform(0.7, 1.0)
            
            # Calcular potência (baseado na capacidade da usina)
            potencia_max = float(usina.capacidade_kwp) * 0.85  # 85% de eficiência
            potencia_atual = potencia_max * fator_geracao
            
            # Energia acumulada do dia (integral da potência)
            energia_dia = potencia_max * fator_geracao * (hora - 6 + 0.5)
            
            # Dados ambientais
            irradiancia = 1000 * fator_geracao + random.uniform(-50, 50)
            temp_modulo = 25 + (fator_geracao * 20) + random.uniform(-3, 3)
            temp_ambiente = 22 + (fator_geracao * 8) + random.uniform(-2, 2)
            
            # Sistema elétrico
            tensao = 380 + random.uniform(-10, 10)
            corrente = (potencia_atual * 1000) / (tensao * 1.732) if potencia_atual > 0 else 0
            frequencia = 60 + random.uniform(-0.2, 0.2)
            
            # Eficiência
            eficiencia = 85 + random.uniform(-5, 5)
            fator_potencia = 0.99 + random.uniform(-0.02, 0.01)
            
            # Status
            if random.random() < 0.05:  # 5% chance de alerta
                status = 'alerta'
            elif random.random() < 0.02:  # 2% chance de offline
                status = 'offline'
                potencia_atual = 0
                energia_dia = 0
            else:
                status = 'online'
            
            leitura = LeituraUsina.objects.create(
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


def criar_alertas_exemplo(usinas):
    """Criar alguns alertas de exemplo"""
    print("\nCriando alertas de exemplo...")
    
    alertas_data = [
        {
            'usina': usinas[0],
            'tipo': 'aviso',
            'categoria': 'temperatura',
            'titulo': 'Temperatura do módulo acima do normal',
            'descricao': 'A temperatura dos módulos está 5°C acima da média. Verificar ventilação.',
        },
        {
            'usina': usinas[1],
            'tipo': 'alerta',
            'categoria': 'eficiencia',
            'titulo': 'Queda de eficiência detectada',
            'descricao': 'Eficiência 10% abaixo do esperado nas últimas 3 horas. Verificar sujeira nos painéis.',
        },
        {
            'usina': usinas[2],
            'tipo': 'critico',
            'categoria': 'comunicacao',
            'titulo': 'Perda de comunicação com inversor',
            'descricao': 'Sem comunicação com o inversor há 15 minutos. Verificar conexão de rede.',
        },
    ]
    
    for alerta_data in alertas_data:
        alerta, created = AlertaUsina.objects.get_or_create(
            titulo=alerta_data['titulo'],
            defaults={
                **alerta_data,
                'timestamp': timezone.now() - timedelta(hours=random.randint(1, 12))
            }
        )
        if created:
            print(f"✓ Alerta criado: {alerta.titulo}")


def main():
    print("=" * 60)
    print("POPULANDO BANCO DE DADOS - MONITORAMENTO SOLAR")
    print("=" * 60)
    
    # Criar usinas
    print("\n1. Criando usinas solares...")
    usinas = criar_usinas()
    
    # Criar leituras históricas
    print("\n2. Criando leituras históricas (últimos 7 dias)...")
    for usina in usinas:
        criar_leituras_historicas(usina, dias=7)
    
    # Criar alertas
    print("\n3. Criando alertas de exemplo...")
    criar_alertas_exemplo(usinas)
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO:")
    print("=" * 60)
    print(f"✓ Usinas criadas: {UsinaSolar.objects.count()}")
    print(f"✓ Leituras criadas: {LeituraUsina.objects.count()}")
    print(f"✓ Alertas criados: {AlertaUsina.objects.count()}")
    print("\n✓ Dados populados com sucesso!")
    print("\nAcesse o dashboard em: http://localhost:8000/solar/")
    print("=" * 60)


if __name__ == '__main__':
    main()
