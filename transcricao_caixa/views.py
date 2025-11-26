from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import FechamentoCaixa, DocumentoTranscrito, Empresa, TipoDocumento, ItemDocumento
from datetime import date


@login_required
def index(request):
    """Página inicial do sistema de transcrição de caixa"""
    # Estatísticas gerais
    total_fechamentos = FechamentoCaixa.objects.count()
    fechamentos_pendentes = FechamentoCaixa.objects.filter(status__in=['rascunho', 'em_processamento', 'aguardando_revisao']).count()
    documentos_pendentes = DocumentoTranscrito.objects.filter(status='pendente').count()
    
    # Fechamentos recentes
    fechamentos_recentes = FechamentoCaixa.objects.all()[:10]
    
    context = {
        'total_fechamentos': total_fechamentos,
        'fechamentos_pendentes': fechamentos_pendentes,
        'documentos_pendentes': documentos_pendentes,
        'fechamentos_recentes': fechamentos_recentes,
    }
    
    return render(request, 'transcricao_caixa/index.html', context)


@login_required
def lista_fechamentos(request):
    """Lista todos os fechamentos de caixa"""
    fechamentos = FechamentoCaixa.objects.select_related('empresa', 'criado_por').all()
    
    # Filtros
    empresa_id = request.GET.get('empresa')
    status = request.GET.get('status')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    if empresa_id:
        fechamentos = fechamentos.filter(empresa_id=empresa_id)
    if status:
        fechamentos = fechamentos.filter(status=status)
    if data_inicio:
        fechamentos = fechamentos.filter(data_fechamento__gte=data_inicio)
    if data_fim:
        fechamentos = fechamentos.filter(data_fechamento__lte=data_fim)
    
    # Empresas para filtro
    empresas = Empresa.objects.filter(ativo=True)
    
    context = {
        'fechamentos': fechamentos,
        'empresas': empresas,
        'status_choices': FechamentoCaixa.STATUS_CHOICES,
    }
    
    return render(request, 'transcricao_caixa/lista_fechamentos.html', context)


@login_required
def novo_fechamento(request):
    """Cria um novo fechamento de caixa"""
    if request.method == 'POST':
        empresa_id = request.POST.get('empresa')
        data_fechamento = request.POST.get('data_fechamento')
        observacoes = request.POST.get('observacoes', '')
        
        try:
            empresa = Empresa.objects.get(id=empresa_id)
            
            # Verificar se já existe fechamento para esta empresa nesta data
            if FechamentoCaixa.objects.filter(empresa=empresa, data_fechamento=data_fechamento).exists():
                messages.error(request, 'Já existe um fechamento para esta empresa nesta data.')
                return redirect('transcricao_caixa:novo_fechamento')
            
            fechamento = FechamentoCaixa.objects.create(
                empresa=empresa,
                data_fechamento=data_fechamento,
                observacoes=observacoes,
                criado_por=request.user
            )
            
            messages.success(request, 'Fechamento criado com sucesso!')
            return redirect('transcricao_caixa:detalhe_fechamento', pk=fechamento.pk)
            
        except Empresa.DoesNotExist:
            messages.error(request, 'Empresa não encontrada.')
            return redirect('transcricao_caixa:novo_fechamento')
    
    empresas = Empresa.objects.filter(ativo=True)
    context = {
        'empresas': empresas,
        'data_hoje': date.today(),
    }
    
    return render(request, 'transcricao_caixa/novo_fechamento.html', context)


@login_required
def detalhe_fechamento(request, pk):
    """Exibe detalhes de um fechamento de caixa"""
    fechamento = get_object_or_404(FechamentoCaixa, pk=pk)
    documentos = fechamento.documentos_transcritos.all()
    
    context = {
        'fechamento': fechamento,
        'documentos': documentos,
    }
    
    return render(request, 'transcricao_caixa/detalhe_fechamento.html', context)


@login_required
def editar_fechamento(request, pk):
    """Edita um fechamento de caixa"""
    fechamento = get_object_or_404(FechamentoCaixa, pk=pk)
    
    if request.method == 'POST':
        fechamento.observacoes = request.POST.get('observacoes', '')
        fechamento.status = request.POST.get('status', fechamento.status)
        
        if request.POST.get('status') == 'concluido' and not fechamento.concluido_em:
            fechamento.concluido_em = timezone.now()
        
        fechamento.save()
        messages.success(request, 'Fechamento atualizado com sucesso!')
        return redirect('transcricao_caixa:detalhe_fechamento', pk=pk)
    
    context = {
        'fechamento': fechamento,
        'status_choices': FechamentoCaixa.STATUS_CHOICES,
    }
    
    return render(request, 'transcricao_caixa/editar_fechamento.html', context)


@login_required
def upload_documento(request, fechamento_id):
    """Upload de documento para transcrição"""
    fechamento = get_object_or_404(FechamentoCaixa, pk=fechamento_id)
    
    if request.method == 'POST':
        imagem = request.FILES.get('imagem')
        tipo_documento_id = request.POST.get('tipo_documento')
        tipo_movimento = request.POST.get('tipo_movimento', 'entrada')
        
        if imagem:
            tipo_documento = None
            if tipo_documento_id:
                tipo_documento = TipoDocumento.objects.get(id=tipo_documento_id)
            
            documento = DocumentoTranscrito.objects.create(
                fechamento=fechamento,
                tipo_documento=tipo_documento,
                tipo_movimento=tipo_movimento,
                imagem=imagem,
                status='pendente'
            )
            
            # Atualizar status do fechamento
            if fechamento.status == 'rascunho':
                fechamento.status = 'em_processamento'
                fechamento.save()
            
            messages.success(request, 'Documento enviado com sucesso!')
            
            # Verificar se deve processar automaticamente
            if request.POST.get('processar_automatico'):
                return redirect('transcricao_caixa:processar_documento', pk=documento.pk)
            
            return redirect('transcricao_caixa:detalhe_fechamento', pk=fechamento_id)
    
    tipos_documento = TipoDocumento.objects.filter(ativo=True)
    
    context = {
        'fechamento': fechamento,
        'tipos_documento': tipos_documento,
    }
    
    return render(request, 'transcricao_caixa/upload_documento.html', context)


@login_required
def processar_documento(request, pk):
    """Processa um documento com OCR (placeholder - implementar lógica de OCR)"""
    documento = get_object_or_404(DocumentoTranscrito, pk=pk)
    
    # TODO: Implementar lógica de OCR aqui
    # Por enquanto, apenas marca como processado com dados de exemplo
    
    documento.status = 'processando'
    documento.save()
    
    # Simulação de processamento OCR
    # Em produção, usar Tesseract, Google Vision API, AWS Textract, etc.
    documento.texto_completo = "Texto extraído da imagem (OCR não implementado ainda)"
    documento.confianca_ocr = 85.5
    documento.status = 'processado'
    documento.processado_em = timezone.now()
    documento.save()
    
    # Atualizar status do fechamento
    documento.fechamento.calcular_totais()
    
    messages.success(request, 'Documento processado! Por favor, revise os dados extraídos.')
    return redirect('transcricao_caixa:revisar_documento', pk=pk)


@login_required
def revisar_documento(request, pk):
    """Revisa e edita dados de um documento transcrito"""
    documento = get_object_or_404(DocumentoTranscrito, pk=pk)
    
    if request.method == 'POST':
        # Atualizar dados do documento
        documento.numero_documento = request.POST.get('numero_documento', '')
        documento.data_documento = request.POST.get('data_documento')
        documento.valor_total = request.POST.get('valor_total', 0)
        documento.observacoes = request.POST.get('observacoes', '')
        
        # Marcar como revisado
        documento.marcar_como_revisado(request.user)
        
        messages.success(request, 'Documento revisado com sucesso!')
        return redirect('transcricao_caixa:detalhe_fechamento', pk=documento.fechamento.pk)
    
    context = {
        'documento': documento,
    }
    
    return render(request, 'transcricao_caixa/revisar_documento.html', context)


@login_required
def editar_documento(request, pk):
    """Edita manualmente um documento"""
    documento = get_object_or_404(DocumentoTranscrito, pk=pk)
    
    if request.method == 'POST':
        documento.tipo_documento_id = request.POST.get('tipo_documento')
        documento.tipo_movimento = request.POST.get('tipo_movimento')
        documento.numero_documento = request.POST.get('numero_documento', '')
        documento.data_documento = request.POST.get('data_documento')
        documento.valor_total = request.POST.get('valor_total', 0)
        documento.observacoes = request.POST.get('observacoes', '')
        documento.correcoes_manuais = request.POST.get('correcoes_manuais', '')
        
        documento.save()
        documento.fechamento.calcular_totais()
        
        messages.success(request, 'Documento atualizado com sucesso!')
        return redirect('transcricao_caixa:detalhe_fechamento', pk=documento.fechamento.pk)
    
    tipos_documento = TipoDocumento.objects.filter(ativo=True)
    
    context = {
        'documento': documento,
        'tipos_documento': tipos_documento,
    }
    
    return render(request, 'transcricao_caixa/editar_documento.html', context)


@login_required
def processar_lote(request):
    """API para processar vários documentos em lote"""
    if request.method == 'POST':
        fechamento_id = request.POST.get('fechamento_id')
        
        documentos = DocumentoTranscrito.objects.filter(
            fechamento_id=fechamento_id,
            status='pendente'
        )
        
        count = 0
        for doc in documentos:
            # TODO: Implementar processamento OCR real
            doc.status = 'processado'
            doc.processado_em = timezone.now()
            doc.save()
            count += 1
        
        return JsonResponse({
            'success': True,
            'processados': count,
            'mensagem': f'{count} documento(s) processado(s) com sucesso!'
        })
    
    return JsonResponse({'success': False, 'mensagem': 'Método não permitido'})


@login_required
def obter_dados_documento(request, pk):
    """API para obter dados de um documento em JSON"""
    documento = get_object_or_404(DocumentoTranscrito, pk=pk)
    
    dados = {
        'id': documento.id,
        'numero_documento': documento.numero_documento,
        'data_documento': documento.data_documento.isoformat() if documento.data_documento else None,
        'valor_total': float(documento.valor_total),
        'texto_completo': documento.texto_completo,
        'confianca_ocr': documento.confianca_ocr,
        'status': documento.status,
        'dados_extraidos': documento.dados_extraidos,
    }
    
    return JsonResponse(dados)
