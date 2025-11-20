from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Q, Max
from django.db import models
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import timedelta

from .models import (
    Funcionario, PerfilGestor, Produto, OperacaoVenda, ItemVenda,
    DeteccaoProduto, Incidente, EvidenciaIncidente, Alerta,
    Camera, CameraStatus, ImagemProduto
)
from .serializers import (
    FuncionarioSerializer, PerfilGestorSerializer, ProdutoSerializer,
    OperacaoVendaSerializer, ItemVendaSerializer, DeteccaoProdutoSerializer,
    IncidenteSerializer, EvidenciaIncidenteSerializer, AlertaSerializer,
    CameraSerializer, CameraStatusSerializer
)
from .utils import (
    get_user_permissions, processar_upload_multiplo, definir_imagem_referencia
)


# ==============================================
# 🔐 AUTENTICAÇÃO
# ==============================================

def login_view(request):
    """Página de login"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bem-vindo, {user.get_full_name() or user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Usuário ou senha inválidos!')
    
    return render(request, 'verifik/login.html')


def logout_view(request):
    """Logout do sistema"""
    logout(request)
    messages.info(request, 'Você saiu do sistema.')
    return redirect('login')


# ==============================================
# 📄 VIEWS HTML
# ==============================================

@login_required(login_url='login')
def home(request):
    """Página inicial do VerifiK - Dashboard com estatísticas"""
    agora = timezone.now()
    inicio_dia = agora - timedelta(days=1)
    
    # Estatísticas gerais
    estatisticas = {
        'total_produtos': Produto.objects.filter(ativo=True).count(),
        'total_cameras': Camera.objects.filter(ativa=True).count(),
        'total_funcionarios': Funcionario.objects.filter(ativo=True).count(),
        'vendas_hoje': OperacaoVenda.objects.filter(
            data_hora__gte=inicio_dia,
            status='CONCLUIDA'
        ).count(),
        'deteccoes_hoje': DeteccaoProduto.objects.filter(
            data_hora_deteccao__gte=inicio_dia
        ).count(),
        'incidentes_abertos': Incidente.objects.filter(
            status__in=['ABERTO', 'EM_ANALISE']
        ).count(),
    }
    
    # Dados complementares
    ultimos_incidentes = Incidente.objects.select_related(
        'deteccao', 'deteccao__produto_identificado', 'deteccao__camera'
    ).order_by('-created_at')[:5]
    
    produtos_top = DeteccaoProduto.objects.filter(
        data_hora_deteccao__gte=inicio_dia,
        produto_identificado__isnull=False
    ).values(
        'produto_identificado__descricao_produto'
    ).annotate(total=Count('id')).order_by('-total')[:5]
    
    # Permissões do usuário
    permissions = get_user_permissions(request.user)
    
    context = {
        **estatisticas,
        'ultimos_incidentes': ultimos_incidentes,
        'produtos_top': produtos_top,
        **permissions,
    }
    
    return render(request, 'verifik/home.html', context)


@login_required(login_url='login')
def produtos_lista(request):
    """Lista de produtos com imagens e filtros"""
    produtos = Produto.objects.prefetch_related('imagens_treino').filter(ativo=True)
    
    # Filtros
    tipo_filtro = request.GET.get('tipo')
    busca = request.GET.get('q')
    imagens_filtro = request.GET.get('imagens')
    
    if tipo_filtro:
        produtos = produtos.filter(tipo__icontains=tipo_filtro)
    
    if busca:
        produtos = produtos.filter(
            Q(descricao_produto__icontains=busca) |
            Q(marca__icontains=busca) |
            Q(codigo_barras__icontains=busca)
        )
    
    # Filtro por imagens
    if imagens_filtro == 'com':
        produtos = produtos.exclude(imagens_treino__isnull=True).distinct()
    elif imagens_filtro == 'sem':
        produtos = produtos.filter(imagens_treino__isnull=True)
    
    permissions = get_user_permissions(request.user)
    
    context = {
        'produtos': produtos,
        'tipo_filtro': tipo_filtro,
        'busca': busca,
        'imagens_filtro': imagens_filtro,
        **permissions,
    }
    
    return render(request, 'verifik/produtos_lista.html', context)


@login_required(login_url='login')
def produto_detalhe(request, pk):
    """Detalhes completos do produto com estatísticas e imagens"""
    produto = get_object_or_404(Produto, pk=pk)
    imagens_treino = produto.imagens_treino.filter(ativa=True).order_by('ordem', 'id')
    
    # Estatísticas
    estatisticas = {
        'total_deteccoes': DeteccaoProduto.objects.filter(produto_identificado=produto).count(),
        'total_vendas': ItemVenda.objects.filter(produto=produto).aggregate(
            total=Sum('quantidade')
        )['total'] or 0,
    }
    
    permissions = get_user_permissions(request.user)
    
    context = {
        'produto': produto,
        'imagens_treino': imagens_treino,
        **estatisticas,
        **permissions,
    }
    
    return render(request, 'verifik/produto_detalhe.html', context)


@login_required(login_url='login')
def adicionar_imagem(request, produto_id):
    """Adicionar múltiplas imagens de treino para um produto (apenas ADMIN)"""
    permissions = get_user_permissions(request.user)
    
    if not permissions['is_admin']:
        messages.error(request, 'Você não tem permissão para adicionar imagens.')
        return redirect('produto_detalhe', pk=produto_id)
    
    if request.method != 'POST':
        messages.error(request, 'Método inválido.')
        return redirect('produto_detalhe', pk=produto_id)
    
    produto = get_object_or_404(Produto, pk=produto_id)
    imagens = request.FILES.getlist('imagens')
    
    if not imagens:
        messages.error(request, 'Nenhuma imagem foi enviada.')
        return redirect('produto_detalhe', pk=produto_id)
    
    descricao = request.POST.get('descricao', '')
    
    # Processar upload usando utility
    total_adicionadas, primeira_imagem, erros = processar_upload_multiplo(
        produto, imagens, descricao
    )
    
    # Definir imagem de referência se necessário
    if primeira_imagem:
        definir_imagem_referencia(produto, primeira_imagem)
    
    # Mensagens de feedback
    if erros:
        for erro in erros:
            messages.warning(request, f'Erro: {erro}')
    
    if total_adicionadas > 0:
        messages.success(request, 
            f'✅ {total_adicionadas} imagem(ns) adicionada(s) com sucesso! '
            f'Total: {produto.imagens_treino.count()}'
        )
    else:
        messages.error(request, 'Nenhuma imagem foi adicionada.')
    
    return redirect('produto_detalhe', pk=produto_id)


@login_required(login_url='login')
def remover_imagem(request, imagem_id):
    """Remover imagem de treino (apenas ADMIN)"""
    permissions = get_user_permissions(request.user)
    
    if not permissions['is_admin']:
        messages.error(request, 'Você não tem permissão para remover imagens.')
        return redirect('home')
    
    imagem = get_object_or_404(ImagemProduto, pk=imagem_id)
    produto_id = imagem.produto.id
    
    try:
        # Deletar arquivo físico e registro do banco
        imagem.imagem.delete(save=False)
        imagem.delete()
        messages.success(request, 'Imagem removida com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao remover imagem: {str(e)}')
    
    return redirect('produto_detalhe', pk=produto_id)


# ==============================================
# 🔌 API REST VIEWSETS
# ==============================================


class FuncionarioViewSet(viewsets.ModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ativo', 'cargo']
    search_fields = ['nome_completo', 'matricula', 'cpf']
    ordering_fields = ['nome_completo', 'data_admissao']
    
    @action(detail=True, methods=['get'])
    def estatisticas(self, request, pk=None):
        """Estatísticas de um funcionário específico"""
        funcionario = self.get_object()
        
        stats = {
            'total_vendas': funcionario.operacaovenda_set.count(),
            'total_incidentes': funcionario.incidente_set.count(),
            'incidentes_confirmados': funcionario.incidente_set.filter(status='CONFIRMADO').count(),
            'valor_total_perdido': funcionario.incidente_set.filter(
                status='CONFIRMADO'
            ).aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0,
        }
        
        if stats['total_vendas'] > 0:
            stats['taxa_erro'] = (stats['incidentes_confirmados'] / stats['total_vendas']) * 100
        else:
            stats['taxa_erro'] = 0
        
        return Response(stats)


class PerfilGestorViewSet(viewsets.ModelViewSet):
    queryset = PerfilGestor.objects.all()
    serializer_class = PerfilGestorSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['nivel_acesso']


class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['ativo', 'tipo', 'marca']
    search_fields = ['nome', 'codigo_barras']
    
    @action(detail=True, methods=['get'])
    def analise(self, request, pk=None):
        """Análise de vendas vs detecções de um produto"""
        produto = self.get_object()
        
        vendas = produto.itemvenda_set.aggregate(
            total_vendas=Count('id'),
            quantidade_vendida=Sum('quantidade')
        )
        
        deteccoes = produto.deteccaoproduto_set.count()
        
        incidentes = Incidente.objects.filter(
            deteccao__produto_identificado=produto,
            tipo='PRODUTO_NAO_REGISTRADO',
            status='CONFIRMADO'
        ).count()
        
        return Response({
            'produto': self.get_serializer(produto).data,
            'vendas_registradas': vendas['total_vendas'] or 0,
            'quantidade_vendida': vendas['quantidade_vendida'] or 0,
            'vezes_detectado': deteccoes,
            'vezes_nao_registrado': incidentes,
            'possivel_perda': float(produto.preco) * incidentes
        })


class OperacaoVendaViewSet(viewsets.ModelViewSet):
    queryset = OperacaoVenda.objects.all()
    serializer_class = OperacaoVendaSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'funcionario']
    search_fields = ['numero_venda']
    ordering_fields = ['data_hora', 'valor_total']


class ItemVendaViewSet(viewsets.ModelViewSet):
    queryset = ItemVenda.objects.all()
    serializer_class = ItemVendaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['operacao', 'produto']


class DeteccaoProdutoViewSet(viewsets.ModelViewSet):
    queryset = DeteccaoProduto.objects.all()
    serializer_class = DeteccaoProdutoSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['camera', 'metodo_deteccao', 'produto_identificado']
    ordering_fields = ['data_hora_deteccao', 'confianca']


class IncidenteViewSet(viewsets.ModelViewSet):
    queryset = Incidente.objects.all()
    serializer_class = IncidenteSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'tipo', 'funcionario', 'camera']
    search_fields = ['codigo_incidente', 'descricao']
    ordering_fields = ['data_hora_ocorrencia', 'valor_estimado']
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Dashboard com estatísticas gerais de incidentes"""
        hoje = timezone.now().date()
        
        total = Incidente.objects.count()
        pendentes = Incidente.objects.filter(status='PENDENTE').count()
        confirmados = Incidente.objects.filter(status='CONFIRMADO').count()
        
        hoje_count = Incidente.objects.filter(
            data_hora_ocorrencia__date=hoje
        ).count()
        
        valor_total = Incidente.objects.filter(
            status='CONFIRMADO'
        ).aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0
        
        por_tipo = Incidente.objects.values('tipo').annotate(
            total=Count('id')
        ).order_by('-total')
        
        por_funcionario = Incidente.objects.filter(
            status='CONFIRMADO'
        ).values(
            'funcionario__nome_completo'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:5]
        
        return Response({
            'total_incidentes': total,
            'pendentes': pendentes,
            'confirmados': confirmados,
            'hoje': hoje_count,
            'valor_total_perdido': float(valor_total),
            'por_tipo': list(por_tipo),
            'top_funcionarios': list(por_funcionario)
        })
    
    @action(detail=True, methods=['post'])
    def analisar(self, request, pk=None):
        """Marcar incidente como analisado"""
        incidente = self.get_object()
        incidente.analisado_por = request.user
        incidente.data_analise = timezone.now()
        incidente.status = request.data.get('status', 'EM_INVESTIGACAO')
        incidente.observacoes_analise = request.data.get('observacoes', '')
        incidente.save()
        
        return Response(self.get_serializer(incidente).data)


class EvidenciaIncidenteViewSet(viewsets.ModelViewSet):
    queryset = EvidenciaIncidente.objects.all()
    serializer_class = EvidenciaIncidenteSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['incidente', 'tipo']


class AlertaViewSet(viewsets.ModelViewSet):
    queryset = Alerta.objects.all()
    serializer_class = AlertaSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tipo', 'prioridade', 'canal', 'status', 'destinatario']
    ordering_fields = ['data_criacao', 'prioridade']
    
    @action(detail=True, methods=['post'])
    def marcar_lido(self, request, pk=None):
        """Marcar alerta como lido"""
        alerta = self.get_object()
        alerta.status = 'LIDO'
        alerta.data_leitura = timezone.now()
        alerta.save()
        
        return Response(self.get_serializer(alerta).data)


class CameraViewSet(viewsets.ModelViewSet):
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'ativa', 'localizacao']
    search_fields = ['nome', 'localizacao', 'ip_address']
    
    @action(detail=False, methods=['get'])
    def status_geral(self, request):
        """Status geral de todas as câmeras"""
        total = Camera.objects.count()
        ativas = Camera.objects.filter(ativa=True, status='ATIVA').count()
        inativas = Camera.objects.filter(Q(ativa=False) | Q(status='INATIVA')).count()
        erro = Camera.objects.filter(status='ERRO').count()
        
        # Câmeras sem conexão recente (5 minutos)
        limite = timezone.now() - timedelta(minutes=5)
        sem_conexao = Camera.objects.filter(
            ultima_conexao__lt=limite,
            ativa=True
        ).count()
        
        return Response({
            'total': total,
            'ativas': ativas,
            'inativas': inativas,
            'com_erro': erro,
            'sem_conexao_recente': sem_conexao
        })
    
    @action(detail=True, methods=['get'])
    def historico(self, request, pk=None):
        """Histórico de status de uma câmera"""
        camera = self.get_object()
        dias = int(request.query_params.get('dias', 7))
        
        limite = timezone.now() - timedelta(days=dias)
        historico = camera.historico_status.filter(
            data_hora__gte=limite
        ).order_by('-data_hora')
        
        serializer = CameraStatusSerializer(historico, many=True)
        return Response(serializer.data)


class CameraStatusViewSet(viewsets.ModelViewSet):
    queryset = CameraStatus.objects.all()
    serializer_class = CameraStatusSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['camera', 'status']
    ordering_fields = ['data_hora']
