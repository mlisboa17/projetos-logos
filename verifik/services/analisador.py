"""
Sistema de Comparação e Geração Automática de Incidentes

Compara produtos detectados por câmera com vendas registradas no PDV
e cria incidentes automaticamente quando há divergências.
"""

from django.utils import timezone
from datetime import timedelta
from ..models import (
    DeteccaoProduto, OperacaoVenda, Incidente, EvidenciaIncidente,
    Alerta, Funcionario
)


class AnalisadorIncidentes:
    """Analisa detecções e cria incidentes quando necessário"""
    
    JANELA_TEMPO_SEGUNDOS = 30  # Janela de tempo para comparar (30 segundos)
    CONFIANCA_MINIMA = 80  # Confiança mínima da IA para considerar
    
    def __init__(self):
        self.incidentes_criados = []
    
    def analisar_deteccao(self, deteccao):
        """
        Analisa uma detecção e verifica se há venda correspondente.
        
        Args:
            deteccao (DeteccaoProduto): Detecção a ser analisada
            
        Returns:
            Incidente ou None
        """
        # Verificar confiança mínima
        if deteccao.confianca < self.CONFIANCA_MINIMA:
            print(f"⚠️  Detecção {deteccao.id} ignorada - confiança baixa ({deteccao.confianca}%)")
            return None
        
        # Produto não identificado
        if not deteccao.produto_identificado:
            print(f"⚠️  Detecção {deteccao.id} - produto não identificado")
            return None
        
        # Buscar vendas próximas no tempo
        inicio = deteccao.data_hora_deteccao - timedelta(seconds=self.JANELA_TEMPO_SEGUNDOS)
        fim = deteccao.data_hora_deteccao + timedelta(seconds=self.JANELA_TEMPO_SEGUNDOS)
        
        vendas_proximas = OperacaoVenda.objects.filter(
            data_hora__gte=inicio,
            data_hora__lte=fim,
            status='CONCLUIDA'
        )
        
        # Nenhuma venda encontrada
        if not vendas_proximas.exists():
            return self._criar_incidente_produto_nao_registrado(deteccao)
        
        # Verificar se o produto detectado está em alguma venda
        produto_encontrado = False
        for venda in vendas_proximas:
            if venda.itens.filter(produto=deteccao.produto_identificado).exists():
                produto_encontrado = True
                print(f"✅ Produto {deteccao.produto_identificado.descricao_produto} encontrado na venda {venda.numero_venda}")
                break
        
        if not produto_encontrado:
            # Produto detectado não está em nenhuma venda próxima
            return self._criar_incidente_produto_diferente(deteccao, vendas_proximas.first())
        
        return None
    
    def _criar_incidente_produto_nao_registrado(self, deteccao):
        """Cria incidente quando produto é detectado mas não há venda"""
        
        # Verificar se já existe incidente para esta detecção
        if Incidente.objects.filter(deteccao=deteccao).exists():
            return None
        
        # Gerar código único
        codigo = f"INC{Incidente.objects.count() + 1:06d}"
        
        incidente = Incidente.objects.create(
            codigo_incidente=codigo,
            tipo='PRODUTO_NAO_REGISTRADO',
            status='PENDENTE',
            camera=deteccao.camera,
            deteccao=deteccao,
            data_hora_ocorrencia=deteccao.data_hora_deteccao,
            descricao=f"Produto '{deteccao.produto_identificado.descricao_produto}' detectado pela câmera mas não registrado no PDV. "
                     f"Confiança da IA: {deteccao.confianca}%",
            valor_estimado=deteccao.produto_identificado.preco if deteccao.produto_identificado else 0
        )
        
        print(f"🚨 INCIDENTE CRIADO: {codigo} - Produto não registrado")
        self.incidentes_criados.append(incidente)
        
        # Criar alerta
        self._criar_alerta(incidente)
        
        return incidente
    
    def _criar_incidente_produto_diferente(self, deteccao, venda):
        """Cria incidente quando produto detectado é diferente do registrado"""
        
        # Verificar se já existe incidente para esta detecção
        if Incidente.objects.filter(deteccao=deteccao).exists():
            return None
        
        codigo = f"INC{Incidente.objects.count() + 1:06d}"
        
        # Listar produtos da venda
        produtos_venda = [item.produto.descricao_produto for item in venda.itens.all()]
        
        incidente = Incidente.objects.create(
            codigo_incidente=codigo,
            tipo='PRODUTO_DIFERENTE',
            status='PENDENTE',
            funcionario=venda.funcionario,
            operacao_venda=venda,
            camera=deteccao.camera,
            deteccao=deteccao,
            data_hora_ocorrencia=deteccao.data_hora_deteccao,
            descricao=f"Produto detectado: '{deteccao.produto_identificado.descricao_produto}'. "
                     f"Produtos registrados na venda {venda.numero_venda}: {', '.join(produtos_venda)}. "
                     f"Confiança da IA: {deteccao.confianca}%",
            valor_estimado=deteccao.produto_identificado.preco if deteccao.produto_identificado else 0
        )
        
        print(f"🚨 INCIDENTE CRIADO: {codigo} - Produto diferente do registrado")
        self.incidentes_criados.append(incidente)
        
        # Criar alerta
        self._criar_alerta(incidente)
        
        return incidente
    
    def _criar_alerta(self, incidente):
        """Cria alerta para notificar gestores"""
        from django.contrib.auth.models import User
        from ..models import PerfilGestor
        
        # Buscar gestores que recebem alertas
        gestores = PerfilGestor.objects.filter(receber_alertas_email=True)
        
        for perfil_gestor in gestores:
            Alerta.objects.create(
                tipo='INCIDENTE',
                prioridade='ALTA',
                canal='EMAIL',
                status='PENDENTE',
                destinatario=perfil_gestor.usuario,
                titulo=f'Incidente Detectado: {incidente.codigo_incidente}',
                mensagem=f"{incidente.get_tipo_display()} detectado.\n\n"
                        f"Câmera: {incidente.camera.nome if incidente.camera else 'N/A'}\n"
                        f"Descrição: {incidente.descricao}\n"
                        f"Valor estimado: R$ {incidente.valor_estimado:.2f}\n\n"
                        f"Acesse o painel para mais detalhes.",
                incidente=incidente
            )
            
            print(f"📢 Alerta criado para {perfil_gestor.usuario.get_full_name()}")
    
    def processar_deteccoes_pendentes(self):
        """Processa todas as detecções que ainda não geraram incidentes"""
        # Buscar detecções recentes sem incidente
        limite = timezone.now() - timedelta(hours=24)
        
        deteccoes_pendentes = DeteccaoProduto.objects.filter(
            data_hora_deteccao__gte=limite,
            confianca__gte=self.CONFIANCA_MINIMA
        ).exclude(
            incidente__isnull=False
        )
        
        print(f"\n🔍 Analisando {deteccoes_pendentes.count()} detecções pendentes...")
        
        for deteccao in deteccoes_pendentes:
            self.analisar_deteccao(deteccao)
        
        print(f"\n✅ Análise concluída: {len(self.incidentes_criados)} incidentes criados")
        
        return self.incidentes_criados


def analisar_deteccao_automatica(deteccao_id):
    """
    Função auxiliar para analisar uma detecção específica.
    Pode ser chamada por sinais ou tasks.
    """
    try:
        deteccao = DeteccaoProduto.objects.get(id=deteccao_id)
        analisador = AnalisadorIncidentes()
        return analisador.analisar_deteccao(deteccao)
    except DeteccaoProduto.DoesNotExist:
        print(f"❌ Detecção {deteccao_id} não encontrada")
        return None


def processar_todas_deteccoes():
    """
    Processa todas as detecções pendentes.
    Útil para rodar como comando ou job agendado.
    """
    analisador = AnalisadorIncidentes()
    return analisador.processar_deteccoes_pendentes()
