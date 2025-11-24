from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Q, Max
from django.db import models
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import timedelta

from .models import (
    Funcionario, PerfilGestor, ProdutoMae, CodigoBarrasProdutoMae, OperacaoVenda, ItemVenda,
    DeteccaoProduto, Incidente, EvidenciaIncidente, Alerta,
    Camera, CameraStatus, ImagemProduto
)
from .forms import ProdutoMaeForm, CodigoBarrasFormSet, ImagemProdutoFormSet
from .serializers import (
    FuncionarioSerializer, PerfilGestorSerializer, ProdutoMaeSerializer, CodigoBarrasProdutoMaeSerializer,
    OperacaoVendaSerializer, ItemVendaSerializer, DeteccaoProdutoSerializer,
    IncidenteSerializer, EvidenciaIncidenteSerializer, AlertaSerializer,
    CameraSerializer, CameraStatusSerializer
)
from .utils import (
    get_user_permissions, processar_upload_multiplo, definir_imagem_referencia
)




# ==============================================
# 📄 VIEWS HTML
# ==============================================

@login_required
def home(request):
    """Página inicial do VerifiK - Dashboard com estatísticas"""
    
    # Verificar se usuário tem acesso ao VerifiK
    if not request.user.active_organization:
        messages.warning(request, 'Selecione uma organização para acessar o VerifiK.')
        return redirect('/')
    
    # Filtrar por organização ativa
    org = request.user.active_organization
    
    agora = timezone.now()
    inicio_dia = agora - timedelta(days=1)
    
    # Estatísticas gerais da organização
    estatisticas = {
        'total_produtos': ProdutoMae.objects.filter(ativo=True).count(),
        'total_cameras': Camera.objects.filter(organization=org, ativa=True).count(),
        'total_funcionarios': Funcionario.objects.filter(organization=org, ativo=True).count(),
        'vendas_hoje': OperacaoVenda.objects.filter(
            organization=org,
            data_hora__gte=inicio_dia,
            status='CONCLUIDA'
        ).count(),
        'deteccoes_hoje': DeteccaoProduto.objects.filter(
            camera__organization=org,
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
    produtos = ProdutoMae.objects.prefetch_related('imagens_treino', 'codigos_barras').filter(ativo=True)
    
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
            Q(codigos_barras__codigo__icontains=busca)
        ).distinct()
    
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
    produto = get_object_or_404(ProdutoMae, pk=pk)
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


@login_required
def produto_criar(request):
    """Criar novo produto com códigos e imagens"""
    if request.method == 'POST':
        form = ProdutoMaeForm(request.POST, request.FILES)
        codigos_formset = CodigoBarrasFormSet(request.POST, prefix='codigos')
        imagens_formset = ImagemProdutoFormSet(request.POST, request.FILES, prefix='imagens')
        
        if form.is_valid() and codigos_formset.is_valid() and imagens_formset.is_valid():
            produto = form.save()
            
            # Salvar códigos de barras
            codigos_formset.instance = produto
            codigos_formset.save()
            
            # Salvar imagens
            imagens_formset.instance = produto
            imagens_formset.save()
            
            messages.success(request, f'Produto "{produto.descricao_produto}" criado com sucesso!')
            return redirect('verifik_produto_editar', pk=produto.pk)
    else:
        form = ProdutoMaeForm()
        codigos_formset = CodigoBarrasFormSet(prefix='codigos')
        imagens_formset = ImagemProdutoFormSet(prefix='imagens')
    
    context = {
        'form': form,
        'codigos_formset': codigos_formset,
        'imagens_formset': imagens_formset,
        'titulo': 'Novo Produto'
    }
    return render(request, 'verifik/produto_form.html', context)


@login_required
def produto_editar(request, pk):
    """Editar produto existente com códigos e imagens"""
    produto = get_object_or_404(ProdutoMae, pk=pk)
    
    if request.method == 'POST':
        form = ProdutoMaeForm(request.POST, request.FILES, instance=produto)
        codigos_formset = CodigoBarrasFormSet(request.POST, instance=produto, prefix='codigos')
        imagens_formset = ImagemProdutoFormSet(request.POST, request.FILES, instance=produto, prefix='imagens')
        
        if form.is_valid() and codigos_formset.is_valid() and imagens_formset.is_valid():
            form.save()
            codigos_formset.save()
            imagens_formset.save()
            
            messages.success(request, f'Produto "{produto.descricao_produto}" atualizado com sucesso!')
            return redirect('verifik_produto_editar', pk=produto.pk)
    else:
        form = ProdutoMaeForm(instance=produto)
        codigos_formset = CodigoBarrasFormSet(instance=produto, prefix='codigos')
        imagens_formset = ImagemProdutoFormSet(instance=produto, prefix='imagens')
    
    context = {
        'form': form,
        'codigos_formset': codigos_formset,
        'imagens_formset': imagens_formset,
        'produto': produto,
        'titulo': f'Editar: {produto.descricao_produto}'
    }
    return render(request, 'verifik/produto_form.html', context)


@login_required(login_url='login')
def adicionar_imagem(request, produto_id):
    """
    Adicionar múltiplas imagens de treino para um produto
    
    O que essa função faz:
    - Permite que admin adicione várias imagens de uma vez
    - Recebe múltiplas imagens via formulário
    - Salva cada imagem no banco de dados
    - Define a primeira imagem como referência se produto não tiver
    """
    permissions = get_user_permissions(request.user)
    
    # Verificar se usuário tem permissão de admin
    if not permissions['is_admin']:
        messages.error(request, 'Você não tem permissão para adicionar imagens.')
        return redirect('verifik_produto_detalhe', pk=produto_id)
    
    # Só aceita POST (quando envia formulário)
    if request.method != 'POST':
        messages.error(request, 'Método inválido.')
        return redirect('verifik_produto_detalhe', pk=produto_id)
    
    # Buscar o produto (usa ProdutoMae agora, não Produto)
    produto = get_object_or_404(ProdutoMae, pk=produto_id)
    
    # Pegar lista de imagens enviadas (pode ser várias)
    imagens = request.FILES.getlist('imagens')
    
    if not imagens:
        messages.error(request, 'Nenhuma imagem foi enviada.')
        return redirect('verifik_produto_detalhe', pk=produto_id)
    
    # Pegar descrição opcional
    descricao = request.POST.get('descricao', '')
    
    # Contador de imagens adicionadas
    total_adicionadas = 0
    erros = []
    primeira_imagem = None
    
    # Processar cada imagem enviada
    for i, imagem_file in enumerate(imagens):
        try:
            # Criar registro de imagem no banco
            imagem = ImagemProduto.objects.create(
                produto=produto,
                imagem=imagem_file,
                descricao=descricao,
                ordem=i + 1,  # Ordem sequencial
                ativa=True
            )
            
            # Guardar primeira imagem para definir como referência
            if i == 0:
                primeira_imagem = imagem
            
            total_adicionadas += 1
            
        except Exception as e:
            erros.append(f'Erro ao processar {imagem_file.name}: {str(e)}')
    
    # Definir primeira imagem como referência se produto não tiver
    if primeira_imagem and not produto.imagem_referencia:
        produto.imagem_referencia = primeira_imagem.imagem
        produto.save()
    
    # Mensagens de feedback
    if erros:
        for erro in erros:
            messages.warning(request, f'⚠️ {erro}')
    
    if total_adicionadas > 0:
        messages.success(request, 
            f'✅ {total_adicionadas} imagem(ns) adicionada(s) com sucesso! '
            f'Total de imagens: {produto.imagens_treino.count()}'
        )
    else:
        messages.error(request, 'Nenhuma imagem foi adicionada.')
    
    # Redirecionar de volta para página de detalhes do produto
    return redirect('verifik_produto_detalhe', pk=produto_id)


@login_required(login_url='login')
def remover_imagem(request, imagem_id):
    """
    Remover imagem de treino
    
    O que essa função faz:
    - Permite que admin remova uma imagem
    - Deleta o arquivo físico da imagem
    - Remove o registro do banco de dados
    """
    permissions = get_user_permissions(request.user)
    
    # Verificar permissão de admin
    if not permissions['is_admin']:
        messages.error(request, 'Você não tem permissão para remover imagens.')
        return redirect('home')
    
    # Buscar a imagem
    imagem = get_object_or_404(ImagemProduto, pk=imagem_id)
    produto_id = imagem.produto.id
    
    try:
        # Deletar arquivo físico e registro do banco
        imagem.imagem.delete(save=False)  # Remove arquivo da pasta media
        imagem.delete()  # Remove registro do banco
        messages.success(request, '🗑️ Imagem removida com sucesso!')
    except Exception as e:
        messages.error(request, f'❌ Erro ao remover imagem: {str(e)}')
    
    # Redirecionar de volta para página do produto
    return redirect('verifik_produto_detalhe', pk=produto_id)


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


class ProdutoMaeViewSet(viewsets.ModelViewSet):
    queryset = ProdutoMae.objects.all()
    serializer_class = ProdutoMaeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['ativo', 'tipo', 'marca']
    search_fields = ['descricao_produto', 'marca', 'codigos_barras__codigo']
    
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
