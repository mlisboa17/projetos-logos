from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models_coleta import ImagemProdutoPendente, LoteFotos
from verifik.models import ProdutoMae
import os
import shutil
import json
from pathlib import Path
from PIL import Image
import numpy as np
import cv2
from ultralytics import YOLO
import pytesseract
import re
from pyzbar.pyzbar import decode as barcode_decode
from verifik.models import CodigoBarrasProdutoMae

# Configurar caminho do Tesseract (Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'



@login_required
def enviar_fotos(request):
    """Interface para funcionários enviarem fotos"""
    
    if request.method == 'POST':
        produto_id = request.POST.get('produto_id')
        observacoes = request.POST.get('observacoes', '')
        arquivos = request.FILES.getlist('fotos')
        bboxes_data = request.POST.get('bboxes_data', '[]')  # JSON com bboxes de cada imagem
        
        if not produto_id or not arquivos:
            messages.error(request, 'Selecione um produto e pelo menos uma foto')
            return redirect('enviar_fotos')
        
        produto = get_object_or_404(ProdutoMae, id=produto_id)
        
        # Parsear bboxes
        try:
            bboxes_list = json.loads(bboxes_data)
        except:
            bboxes_list = []
        
        # Criar lote
        lote = LoteFotos.objects.create(
            nome=f"{produto.descricao_produto} - {timezone.now().strftime('%d/%m/%Y %H:%M')}",
            enviado_por=request.user,
            total_imagens=len(arquivos)
        )
        
        # Salvar imagens com bbox_data
        for idx, arquivo in enumerate(arquivos):
            bbox_data = bboxes_list[idx] if idx < len(bboxes_list) else []
            ImagemProdutoPendente.objects.create(
                produto=produto,
                imagem=arquivo,
                enviado_por=request.user,
                observacoes=observacoes,
                lote=lote,
                bbox_data=json.dumps(bbox_data) if bbox_data else ''
            )
        
        messages.success(request, f'{len(arquivos)} foto(s) enviada(s) com sucesso!')
        return redirect('enviar_fotos')
    
    # GET
    produtos = ProdutoMae.objects.all().order_by('descricao_produto')
    
    # Estatísticas do usuário
    stats = {
        'total_enviadas': ImagemProdutoPendente.objects.filter(enviado_por=request.user).count(),
        'aprovadas': ImagemProdutoPendente.objects.filter(enviado_por=request.user, status='aprovada').count(),
        'pendentes': ImagemProdutoPendente.objects.filter(enviado_por=request.user, status='pendente').count(),
    }
    
    context = {
        'produtos': produtos,
        'stats': stats,
    }
    
    return render(request, 'verifik/enviar_fotos_bbox.html', context)


@login_required
def revisar_fotos(request):
    """Interface para revisar e aprovar fotos (apenas admin)"""
    
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado. Apenas administradores.')
        return redirect('home')
    
    # Filtros
    status_filtro = request.GET.get('status', 'pendente')
    produto_id = request.GET.get('produto')
    
    imagens = ImagemProdutoPendente.objects.all()
    
    if status_filtro:
        imagens = imagens.filter(status=status_filtro)
    
    if produto_id:
        imagens = imagens.filter(produto_id=produto_id)
    
    imagens = imagens.select_related('produto', 'enviado_por', 'aprovado_por')
    
    # Estatísticas
    stats = {
        'total_pendentes': ImagemProdutoPendente.objects.filter(status='pendente').count(),
        'total_aprovadas': ImagemProdutoPendente.objects.filter(status='aprovada').count(),
        'total_rejeitadas': ImagemProdutoPendente.objects.filter(status='rejeitada').count(),
    }
    
    produtos = ProdutoMae.objects.annotate(
        total_pendentes=Count('imagemprodutopendente', filter=Q(imagemprodutopendente__status='pendente'))
    ).filter(total_pendentes__gt=0)
    
    context = {
        'imagens': imagens,
        'stats': stats,
        'produtos_com_pendencias': produtos,
        'status_atual': status_filtro,
    }
    
    return render(request, 'verifik/revisar_fotos.html', context)


def recortar_bbox(imagem_path, bbox_data):
    """
    Recorta a região do bounding box de uma imagem.
    bbox_data: dict com keys 'x', 'y', 'width', 'height' (valores normalizados 0-1)
    Retorna: imagem PIL recortada
    """
    img = Image.open(imagem_path)
    img_width, img_height = img.size
    
    # Converter coordenadas normalizadas para pixels
    # x, y são o CENTRO do bbox
    x_center = bbox_data['x'] * img_width
    y_center = bbox_data['y'] * img_height
    bbox_width = bbox_data['width'] * img_width
    bbox_height = bbox_data['height'] * img_height
    
    # Calcular cantos do bbox
    x1 = int(x_center - bbox_width / 2)
    y1 = int(y_center - bbox_height / 2)
    x2 = int(x_center + bbox_width / 2)
    y2 = int(y_center + bbox_height / 2)
    
    # Garantir que está dentro dos limites da imagem
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(img_width, x2)
    y2 = min(img_height, y2)
    
    # Recortar
    cropped = img.crop((x1, y1, x2, y2))
    return cropped


@login_required
def aprovar_imagem(request, imagem_id):
    """Aprovar uma imagem e mover para a base de treinamento (recortando apenas o bbox)"""
    
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    imagem = get_object_or_404(ImagemProdutoPendente, id=imagem_id)
    
    if request.method == 'POST':
        qualidade = request.POST.get('qualidade', 3)
        observacoes = request.POST.get('observacoes', '')
        
        # Atualizar status
        imagem.status = 'aprovada'
        imagem.aprovado_por = request.user
        imagem.data_aprovacao = timezone.now()
        imagem.qualidade = qualidade
        imagem.observacoes = observacoes
        imagem.save()
        
        # Copiar para base de treinamento
        try:
            # Caminho da base de treinamento
            base_path = Path('assets/dataset/train') / imagem.produto.descricao_produto.replace(' ', '_')
            base_path.mkdir(parents=True, exist_ok=True)
            
            # Nome do arquivo
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            novo_nome = f"{imagem.produto.descricao_produto.replace(' ', '_')}_{timestamp}.jpg"
            destino = base_path / novo_nome
            
            # Verificar se tem bbox_data para recortar
            if imagem.bbox_data:
                try:
                    # Parsear bbox data (pode ter múltiplos bboxes, pegar o primeiro)
                    bboxes = json.loads(imagem.bbox_data)
                    if bboxes:
                        bbox = bboxes[0]  # Pegar primeiro bbox
                        
                        # Recortar apenas a região do bbox
                        img_recortada = recortar_bbox(imagem.imagem.path, bbox)
                        
                        # Salvar imagem recortada
                        img_recortada.save(destino, 'JPEG', quality=95)
                        
                        messages.success(request, f'✅ Imagem aprovada! Bbox recortado e salvo no dataset.')
                    else:
                        # Sem bbox, copiar imagem completa
                        shutil.copy2(imagem.imagem.path, destino)
                        messages.success(request, f'Imagem aprovada e adicionada à base (sem bbox).')
                except (json.JSONDecodeError, KeyError) as e:
                    # Erro ao parsear bbox, copiar imagem completa
                    shutil.copy2(imagem.imagem.path, destino)
                    messages.warning(request, f'Imagem aprovada, mas erro ao recortar bbox. Salva completa.')
            else:
                # Sem bbox_data, copiar imagem completa
                shutil.copy2(imagem.imagem.path, destino)
                messages.success(request, f'Imagem aprovada e adicionada à base de treinamento!')
                
        except Exception as e:
            messages.warning(request, f'Imagem aprovada, mas erro ao processar: {str(e)}')
        
        return redirect('revisar_fotos')
    
    context = {'imagem': imagem}
    return render(request, 'verifik/aprovar_imagem.html', context)


@login_required
def rejeitar_imagem(request, imagem_id):
    """Rejeitar uma imagem"""
    
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    imagem = get_object_or_404(ImagemProdutoPendente, id=imagem_id)
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        
        imagem.status = 'rejeitada'
        imagem.aprovado_por = request.user
        imagem.data_aprovacao = timezone.now()
        imagem.motivo_rejeicao = motivo
        imagem.save()
        
        messages.info(request, 'Imagem rejeitada')
        return redirect('revisar_fotos')
    
    context = {'imagem': imagem}
    return render(request, 'verifik/rejeitar_imagem.html', context)


@login_required
def listar_lotes(request):
    """Lista todos os lotes de fotos"""
    
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado. Apenas administradores.')
        return redirect('home')
    
    lotes = LoteFotos.objects.all().select_related('enviado_por').order_by('-data_criacao')
    
    # Adicionar estatísticas de cada lote
    for lote in lotes:
        lote.imagens_pendentes = lote.imagens.filter(status='pendente').count()
        lote.imagens_aprovadas_count = lote.imagens.filter(status='aprovada').count()
        lote.imagens_rejeitadas_count = lote.imagens.filter(status='rejeitada').count()
    
    context = {
        'lotes': lotes,
        'total_lotes': lotes.count(),
    }
    
    return render(request, 'verifik/lotes_lista.html', context)


@login_required
def detalhe_lote(request, lote_id):
    """Mostra detalhes e imagens de um lote específico, agrupadas por produto"""
    
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    lote = get_object_or_404(LoteFotos, id=lote_id)
    imagens = lote.imagens.all().select_related('produto', 'enviado_por', 'aprovado_por')
    
    # Estatísticas do lote
    stats = {
        'total': imagens.count(),
        'pendentes': imagens.filter(status='pendente').count(),
        'aprovadas': imagens.filter(status='aprovada').count(),
        'rejeitadas': imagens.filter(status='rejeitada').count(),
    }
    
    # Agrupar imagens por produto
    from collections import defaultdict
    imagens_por_produto = defaultdict(lambda: {
        'produto': None,
        'imagens': [],
        'pendentes': 0,
        'aprovadas': 0,
        'rejeitadas': 0,
    })
    
    for imagem in imagens:
        produto_id = imagem.produto.id
        if imagens_por_produto[produto_id]['produto'] is None:
            imagens_por_produto[produto_id]['produto'] = imagem.produto
        
        imagens_por_produto[produto_id]['imagens'].append(imagem)
        
        if imagem.status == 'pendente':
            imagens_por_produto[produto_id]['pendentes'] += 1
        elif imagem.status == 'aprovada':
            imagens_por_produto[produto_id]['aprovadas'] += 1
        elif imagem.status == 'rejeitada':
            imagens_por_produto[produto_id]['rejeitadas'] += 1
    
    # Converter para lista ordenada
    grupos_produtos = sorted(
        imagens_por_produto.values(),
        key=lambda x: x['produto'].descricao_produto
    )
    
    context = {
        'lote': lote,
        'imagens': imagens,
        'stats': stats,
        'grupos_produtos': grupos_produtos,
    }
    
    return render(request, 'verifik/lote_detalhe.html', context)


@login_required
def aprovar_lote_completo(request, lote_id):
    """Aprova todas as imagens pendentes de um lote"""
    
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    lote = get_object_or_404(LoteFotos, id=lote_id)
    imagens_pendentes = lote.imagens.filter(status='pendente')
    
    aprovadas = 0
    erros = 0
    
    for imagem in imagens_pendentes:
        try:
            # Atualizar status
            imagem.status = 'aprovada'
            imagem.aprovado_por = request.user
            imagem.data_aprovacao = timezone.now()
            imagem.qualidade = 3  # Qualidade média
            imagem.save()
            
            # Copiar para base de treinamento
            base_path = Path('assets/dataset/train') / imagem.produto.descricao_produto.replace(' ', '_')
            base_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            novo_nome = f"{imagem.produto.descricao_produto.replace(' ', '_')}_{timestamp}_{imagem.id}.jpg"
            destino = base_path / novo_nome
            
            shutil.copy2(imagem.imagem.path, destino)
            aprovadas += 1
            
        except Exception as e:
            erros += 1
            print(f"Erro ao aprovar imagem {imagem.id}: {e}")
    
    messages.success(request, f'{aprovadas} imagens aprovadas! {erros} erros.')
    return redirect('detalhe_lote', lote_id=lote_id)


@login_required
def aprovar_produto_lote(request, lote_id, produto_id):
    """Aprova todas as imagens pendentes de um produto específico dentro de um lote"""
    
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    lote = get_object_or_404(LoteFotos, id=lote_id)
    produto = get_object_or_404(ProdutoMae, id=produto_id)
    
    imagens_pendentes = lote.imagens.filter(status='pendente', produto=produto)
    
    aprovadas = 0
    erros = 0
    
    for imagem in imagens_pendentes:
        try:
            # Atualizar status
            imagem.status = 'aprovada'
            imagem.aprovado_por = request.user
            imagem.data_aprovacao = timezone.now()
            imagem.qualidade = 3  # Qualidade média
            imagem.save()
            
            # Copiar para base de treinamento
            base_path = Path('assets/dataset/train') / produto.descricao_produto.replace(' ', '_')
            base_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            novo_nome = f"{produto.descricao_produto.replace(' ', '_')}_{timestamp}_{imagem.id}.jpg"
            destino = base_path / novo_nome
            
            # Verificar se tem bbox_data para recortar
            if imagem.bbox_data:
                try:
                    bboxes = json.loads(imagem.bbox_data)
                    if bboxes:
                        bbox = bboxes[0]  # Pegar primeiro bbox
                        
                        # Recortar apenas a região do bbox
                        img_recortada = recortar_bbox(imagem.imagem.path, bbox)
                        img_recortada.save(destino, 'JPEG', quality=95)
                    else:
                        shutil.copy2(imagem.imagem.path, destino)
                except (json.JSONDecodeError, KeyError):
                    shutil.copy2(imagem.imagem.path, destino)
            else:
                shutil.copy2(imagem.imagem.path, destino)
            
            aprovadas += 1
            
        except Exception as e:
            erros += 1
            print(f"Erro ao aprovar imagem {imagem.id}: {e}")
    
    if aprovadas > 0:
        messages.success(request, f'✅ {aprovadas} bboxes de "{produto.descricao_produto}" recortados e salvos no dataset!')
    if erros > 0:
        messages.warning(request, f'⚠️ {erros} erro(s) ao processar imagens.')
    
    return redirect('detalhe_lote', lote_id=lote_id)


# Carregar modelo YOLO uma única vez
YOLO_MODEL = None

def get_yolo_model():
    """Carrega o modelo YOLO (singleton)"""
    global YOLO_MODEL
    if YOLO_MODEL is None:
        model_path = Path(__file__).parent.parent / 'verifik' / 'verifik_yolov8.pt'
        if not model_path.exists():
            # Fallback para modelo genérico
            model_path = Path(__file__).parent.parent / 'yolov8n.pt'
        YOLO_MODEL = YOLO(str(model_path))
    return YOLO_MODEL


def classificar_forma_produto(bbox_img):
    """
    Classifica a forma do produto usando análise de proporções, cores e características
    Retorna: 'lata', 'garrafa', 'long_neck', 'caixa', 'desconhecido'
    """
    try:
        h, w = bbox_img.shape[:2]
        
        # Calcular proporção altura/largura da bbox inteira
        aspect_ratio = h / w if w > 0 else 0
        
        # Análise de cores dominantes (para detectar vidro/metal)
        hsv = cv2.cvtColor(bbox_img, cv2.COLOR_BGR2HSV)
        
        # Detectar cor verde (Heineken, Stella)
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        mask_green = cv2.inRange(hsv, lower_green, upper_green)
        green_ratio = np.sum(mask_green > 0) / (h * w)
        
        # Detectar cor dourada/amarela (cerveja, rótulos)
        lower_yellow = np.array([15, 40, 40])
        upper_yellow = np.array([35, 255, 255])
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
        yellow_ratio = np.sum(mask_yellow > 0) / (h * w)
        
        # Detectar cor vermelha (Amstel, Brahma)
        lower_red1 = np.array([0, 40, 40])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 40, 40])
        upper_red2 = np.array([180, 255, 255])
        mask_red = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)
        red_ratio = np.sum(mask_red > 0) / (h * w)
        
        # Detectar preto (Black Pepsi, garrafas escuras)
        lower_black = np.array([0, 0, 0])
        upper_black = np.array([180, 255, 50])
        mask_black = cv2.inRange(hsv, lower_black, upper_black)
        black_ratio = np.sum(mask_black > 0) / (h * w)
        
        # Detectar reflexo metálico (latas)
        gray = cv2.cvtColor(bbox_img, cv2.COLOR_BGR2GRAY)
        _, bright_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        bright_ratio = np.sum(bright_mask > 0) / (h * w)
        
        # Detectar bordas (garrafas têm mais bordas definidas)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (h * w)
        
        # Lógica de classificação combinada
        forma = 'desconhecido'
        confianca_forma = 0
        
        # Long Neck: muito alto e fino, geralmente verde ou marrom
        if aspect_ratio > 3.0:
            forma = 'long_neck'
            confianca_forma = 90
        elif aspect_ratio > 2.2:
            if green_ratio > 0.1 or black_ratio > 0.3:
                forma = 'long_neck'
                confianca_forma = 85
            else:
                forma = 'garrafa'
                confianca_forma = 75
        # Lata: proporção média, reflexo metálico, mais cilíndrico
        elif 1.3 < aspect_ratio <= 2.2:
            if bright_ratio > 0.05 or (red_ratio > 0.15 and aspect_ratio < 1.8):
                forma = 'lata'
                confianca_forma = 80
            elif green_ratio > 0.15:
                forma = 'long_neck'
                confianca_forma = 70
            else:
                forma = 'garrafa'
                confianca_forma = 60
        # Caixa: mais quadrado ou mais largo que alto
        elif aspect_ratio <= 1.3:
            if aspect_ratio >= 0.7:
                forma = 'lata'  # Lata deitada ou vista de cima
                confianca_forma = 50
            else:
                forma = 'caixa'
                confianca_forma = 70
        
        print(f"🔷 Forma detectada: {forma} (aspect_ratio={aspect_ratio:.2f}, green={green_ratio:.2f}, bright={bright_ratio:.2f})")
        return forma
            
    except Exception as e:
        print(f"Erro ao classificar forma: {e}")
        return 'desconhecido'


def detectar_codigo_barras(bbox_img):
    """
    Detecta código de barras na imagem usando pyzbar
    Retorna (codigo, tipo) ou (None, None) se não encontrado
    """
    try:
        # Tentar detectar código de barras
        barcodes = barcode_decode(bbox_img)
        
        if barcodes:
            for barcode in barcodes:
                codigo = barcode.data.decode('utf-8')
                tipo = barcode.type
                print(f"✅ CÓDIGO DE BARRAS DETECTADO: {codigo} (Tipo: {tipo})")
                return (codigo, tipo)
        
        return (None, None)
        
    except Exception as e:
        print(f"Erro na detecção de código de barras: {e}")
        return (None, None)


def extrair_texto_ocr(bbox_img):
    """
    Extrai texto da região do produto usando OCR
    Retorna lista de palavras-chave encontradas
    Usa múltiplas técnicas de pré-processamento para melhor resultado
    """
    try:
        todas_palavras = set()
        
        # Redimensionar para melhor leitura (mínimo 300px de altura)
        h, w = bbox_img.shape[:2]
        if h < 300:
            scale = 300 / h
            bbox_img = cv2.resize(bbox_img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        gray = cv2.cvtColor(bbox_img, cv2.COLOR_BGR2GRAY)
        
        # TÉCNICA 1: Threshold adaptativo
        thresh1 = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # TÉCNICA 2: Otsu threshold com blur
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh2 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # TÉCNICA 3: CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        _, thresh3 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # TÉCNICA 4: Inversão (para texto claro em fundo escuro)
        thresh4 = cv2.bitwise_not(thresh2)
        
        # TÉCNICA 5: Dilatação para conectar letras quebradas
        kernel = np.ones((2, 2), np.uint8)
        thresh5 = cv2.dilate(thresh2, kernel, iterations=1)
        
        # Rodar OCR em cada versão
        imagens_processar = [thresh1, thresh2, thresh3, thresh4, thresh5, gray]
        
        for img_proc in imagens_processar:
            try:
                # Config para melhor detecção: PSM 6 = bloco uniforme de texto
                texto = pytesseract.image_to_string(img_proc, lang='por+eng', config='--psm 6')
                texto = texto.upper()
                
                # Extrair palavras (3+ letras)
                palavras = re.findall(r'\b[A-Z]{3,}\b', texto)
                
                # Extrair também números com letras (volumes como 350ML)
                volumes = re.findall(r'\b\d+\s*(?:ML|L|LT|G|KG)\b', texto, re.IGNORECASE)
                
                todas_palavras.update(palavras)
                todas_palavras.update([v.upper().replace(' ', '') for v in volumes])
            except:
                continue
        
        # Filtrar palavras comuns/irrelevantes
        palavras_irrelevantes = {'THE', 'AND', 'FOR', 'COM', 'NET', 'IND', 'LTD', 'SAO', 'QUE', 'NAO', 'POR', 'UMA', 'DOS', 'DAS'}
        palavras_filtradas = [p for p in todas_palavras if p not in palavras_irrelevantes and len(p) >= 3]
        
        # === MARCAS CONHECIDAS (Cervejas + Refrigerantes) ===
        marcas_conhecidas = [
            # Cervejas
            'HEINEKEN', 'AMSTEL', 'STELLA', 'BUDWEISER', 'CORONA', 'BRAHMA', 'SKOL', 
            'DEVASSA', 'EISENBAHN', 'LOKAL', 'ANTARCTICA', 'BOHEMIA', 'SPATEN', 'BECKS',
            # Refrigerantes
            'PEPSI', 'COCA COLA', 'GUARANA', 'FANTA', 'SPRITE', 'SCHWEPPES', 'SUKITA', 'KUAT', 'H2OH'
        ]
        
        # === RECIPIENTES ===
        # LATA = 350ml (padrão)
        # LATÃO = 473ml, 550ml (lata grande, comum em cervejas)
        # LONG NECK = 330ml, 355ml (garrafa pequena)
        # GARRAFA = 600ml (vidro)
        # PET = 600ml, 1L, 2L (plástico - refrigerantes)
        recipientes = ['LONG NECK', 'LONGNECK', 'LATA', 'LATAO', 'LATÃO', 'GARRAFA', 'PET']
        
        # === TIPOS DE CERVEJA ===
        tipos_cerveja = [
            'PILSEN', 'PURO MALTE', 'ZERO ALCOOL', 'ZERO', 'BLACK', 'GOLD', 'PUREGOLD',
            'IPA', 'LAGER', 'ALE', 'WEISS', 'PREMIUM', 'EXTRA', 'ORIGINAL', 'MALZBIER'
        ]
        
        # === TIPOS DE REFRIGERANTE ===
        tipos_refri = ['ZERO', 'LIGHT', 'DIET', 'ORIGINAL', 'LARANJA', 'UVA', 'LIMAO', 'CITRUS']
        
        # Lista de prioridade: marcas > recipientes > tipos
        marcas_prioritarias = marcas_conhecidas + recipientes + tipos_cerveja + tipos_refri
        
        # Ordenar: marcas primeiro, depois recipientes, tipos e outras palavras
        resultado = []
        for marca in marcas_prioritarias:
            if marca in palavras_filtradas:
                resultado.append(marca)
                palavras_filtradas.remove(marca)
        resultado.extend(palavras_filtradas)
        
        print(f"📝 OCR extraiu: {resultado[:15]}")
        return resultado[:15]  # Top 15 palavras
        
    except Exception as e:
        print(f"Erro no OCR: {e}")
        return []


def calcular_similaridade(texto1, texto2):
    """Calcula similaridade entre dois textos usando múltiplas técnicas"""
    texto1 = texto1.upper().strip()
    texto2 = texto2.upper().strip()
    
    if not texto1 or not texto2:
        return 0
    
    # 1. Match exato
    if texto1 == texto2:
        return 100
    
    # 2. Contido um no outro
    if texto1 in texto2 or texto2 in texto1:
        return 80
    
    # 3. Calcular Jaccard (palavras em comum)
    palavras1 = set(texto1.split())
    palavras2 = set(texto2.split())
    if palavras1 and palavras2:
        intersecao = len(palavras1 & palavras2)
        uniao = len(palavras1 | palavras2)
        jaccard = (intersecao / uniao) * 100 if uniao > 0 else 0
        if jaccard > 0:
            return jaccard
    
    # 4. Calcular distância de caracteres (simples)
    comum = sum(1 for c in texto1 if c in texto2)
    max_len = max(len(texto1), len(texto2))
    return (comum / max_len) * 60 if max_len > 0 else 0


def sugerir_produto_ia(texto_ocr, forma, produtos_db, codigo_barras=None):
    """
    Sugere produto baseado em código de barras + OCR + forma + banco de dados
    Retorna (produto_id, confianca, razao)
    
    PRIORIDADE:
    1. Código de barras = 99.99% confiança (match perfeito)
    2. OCR + Forma + Volume + Cor = 0-100% confiança (análise multi-critério)
    
    MELHORADO: Busca fuzzy, detecção de marcas parciais, análise de variações
    """
    try:
        # 🔥 PRIORIDADE MÁXIMA: Código de barras
        if codigo_barras:
            try:
                codigo_obj = CodigoBarrasProdutoMae.objects.get(codigo=codigo_barras)
                produto_mae = codigo_obj.produto_mae
                print(f"🎯 MATCH PERFEITO! Código de barras: {codigo_barras} → {produto_mae.descricao_produto}")
                return (produto_mae.id, 99.99, f"🔥 CÓDIGO DE BARRAS: {codigo_barras} (Match Exato)")
            except CodigoBarrasProdutoMae.DoesNotExist:
                print(f"⚠️ Código de barras {codigo_barras} não encontrado no banco")
        
        # ============================================================
        # === MARCAS CONHECIDAS (Cervejas e Refrigerantes) ===
        # ============================================================
        marcas_aliases = {
            # CERVEJAS
            'HEINEKEN': ['HEINEKEN', 'HEIN', 'HNK', 'HEINEK'],
            'AMSTEL': ['AMSTEL', 'AMST', 'AMSTERDAM'],
            'STELLA': ['STELLA', 'ARTOIS', 'STELLA ARTOIS'],
            'BUDWEISER': ['BUDWEISER', 'BUD', 'BUDW'],
            'CORONA': ['CORONA', 'CORON'],
            'BRAHMA': ['BRAHMA', 'BRAH'],
            'SKOL': ['SKOL', 'SK'],
            'LOKAL': ['LOKAL', 'LOCAL'],
            'DEVASSA': ['DEVASSA', 'DEVAS'],
            'EISENBAHN': ['EISENBAHN', 'EISEN'],
            'ANTARCTICA': ['ANTARCTICA', 'ANTARTICA', 'ANTARTC'],
            'BOHEMIA': ['BOHEMIA', 'BOHEM'],
            'ORIGINAL': ['ORIGINAL'],
            'SPATEN': ['SPATEN'],
            'BECKS': ['BECKS', 'BECK'],
            # REFRIGERANTES
            'COCA COLA': ['COCA COLA', 'COCA', 'COLA', 'COCA-COLA', 'COCACOLA'],
            'PEPSI': ['PEPSI', 'PEPS'],
            'GUARANA': ['GUARANA', 'GUARANÁ', 'GUAR'],
            'FANTA': ['FANTA', 'FANT'],
            'SPRITE': ['SPRITE', 'SPRIT'],
            'SCHWEPPES': ['SCHWEPPES', 'SCHWEP'],
            'SUKITA': ['SUKITA'],
            'KUAT': ['KUAT'],
            'H2OH': ['H2OH', 'H2O'],
        }
        
        # ============================================================
        # === RECIPIENTES (com volumes associados) ===
        # ============================================================
        # CERVEJAS:
        #   - LATA = 350ml (padrão)
        #   - LATÃO = 473ml, 550ml (lata grande)
        #   - LONG NECK = 330ml, 355ml (garrafa pequena)
        #   - GARRAFA = 600ml, 1L (garrafa grande)
        # 
        # REFRIGERANTES:
        #   - LATA = 350ml
        #   - PET 600ML = 600ml
        #   - PET 1L = 1000ml
        #   - PET 2L = 2000ml
        recipientes_aliases = {
            'lata': ['LATA', 'LT', 'CAN', 'LATINHA', 'LATAS'],
            'latao': ['LATAO', 'LATÃO', 'LATA GRANDE', 'LATONA'],
            'long neck': ['LONG NECK', 'LONGNECK', 'LONG', 'NECK', 'LN'],
            'garrafa': ['GARRAFA', 'GF', 'BOTTLE', 'GARR', 'VIDRO'],
            'pet': ['PET', 'PLASTICO', 'PLÁSTICO', 'DESCARTAVEL', 'DESCARTÁVEL'],
            'caixa': ['CAIXA', 'CX', 'PACK', 'BOX', 'FARDO', 'ENGRADADO'],
            'ks': ['KS', 'GARRAFA KS'],  # Garrafa retornável pequena
            'litrinho': ['LITRINHO', 'LITRÃO', 'LITRAO'],
        }
        
        # ============================================================
        # === TIPOS DE CERVEJA ===
        # ============================================================
        tipos_cerveja_aliases = {
            'PILSEN': ['PILSEN', 'PILS', 'PILSNER'],
            'PURO MALTE': ['PURO MALTE', 'PUROMALTE', 'PURE MALT'],
            'ZERO ALCOOL': ['ZERO ALCOOL', 'ZERO ÁLCOOL', 'SEM ALCOOL', 'SEM ÁLCOOL', '0,0%', '0.0%', '0%'],
            'ZERO': ['ZERO'],  # Pode ser Zero Açúcar (refri) ou Zero Álcool (cerveja)
            'BLACK': ['BLACK', 'BLK', 'PRETA', 'ESCURA', 'DARK'],
            'GOLD': ['GOLD', 'GOLDEN', 'DOURADA'],
            'PUREGOLD': ['PUREGOLD', 'PURE GOLD'],
            'IPA': ['IPA', 'INDIA PALE ALE'],
            'LAGER': ['LAGER'],
            'WEISS': ['WEISS', 'WEIZEN', 'TRIGO'],
            'PREMIUM': ['PREMIUM', 'EXTRA', 'SPECIAL'],
            'ORIGINAL': ['ORIGINAL', 'ORIG'],
            'MALZBIER': ['MALZBIER', 'MALZ'],
        }
        
        # ============================================================
        # === TIPOS DE REFRIGERANTE ===
        # ============================================================
        tipos_refri_aliases = {
            'ZERO': ['ZERO', 'ZERO AÇUCAR', 'ZERO ACUCAR', 'SEM AÇUCAR', 'SEM ACUCAR'],
            'LIGHT': ['LIGHT', 'DIET', 'DIETA'],
            'ORIGINAL': ['ORIGINAL', 'TRADICIONAL', 'NORMAL'],
            'LARANJA': ['LARANJA', 'ORANGE'],
            'UVA': ['UVA', 'GRAPE'],
            'LIMAO': ['LIMAO', 'LIMÃO', 'LEMON', 'LIMA'],
            'GUARANA': ['GUARANA', 'GUARANÁ'],
            'CITRUS': ['CITRUS', 'CITRICO', 'CÍTRICO'],
        }
        
        # ============================================================
        # === VOLUMES CONHECIDOS ===
        # ============================================================
        volumes_conhecidos = [
            # Latas
            '269ML', '310ML', '350ML',
            # Latão
            '473ML', '550ML',
            # Long Neck
            '330ML', '355ML',
            # Garrafas/PET
            '600ML', 
            '1L', '1LT', '1000ML', '1LITRO',
            '2L', '2LT', '2000ML', '2LITROS', '2LTS',
            '3L', '3LT', '3000ML',
        ]
        
        # ============================================================
        # === MAPEAMENTO VOLUME → RECIPIENTE ===
        # ============================================================
        volume_para_recipiente = {
            # LATA (cerveja e refrigerante)
            '269ML': 'lata',
            '310ML': 'lata',
            '350ML': 'lata',
            # LATÃO (cerveja)
            '473ML': 'latao',
            '550ML': 'latao',
            # LONG NECK (cerveja)
            '330ML': 'long neck',
            '355ML': 'long neck',
            # PET/GARRAFA (refrigerante principalmente)
            '600ML': 'pet',       # PET 600ml
            '1L': 'pet',          # PET 1 Litro
            '1LT': 'pet',
            '1000ML': 'pet',
            '1LITRO': 'pet',
            '2L': 'pet',          # PET 2 Litros
            '2LT': 'pet',
            '2LTS': 'pet',
            '2000ML': 'pet',
            '2LITROS': 'pet',
            '3L': 'pet',
            '3LT': 'pet',
            '3000ML': 'pet',
        }
        
        # Análise multi-critério (se não houver código de barras)
        melhor_match = None
        melhor_score = 0
        melhor_razao = ""
        
        # Concatenar todas as palavras OCR para busca mais fácil
        texto_ocr_str = ' '.join(texto_ocr).upper()
        print(f"📊 Analisando OCR: {texto_ocr_str}")
        print(f"📊 Forma detectada: {forma}")
        
        # Detectar volume no OCR para inferir recipiente
        volume_detectado = None
        recipiente_inferido = None
        for vol in volumes_conhecidos:
            if vol in texto_ocr_str:
                volume_detectado = vol
                recipiente_inferido = volume_para_recipiente.get(vol)
                print(f"📏 Volume detectado: {vol} → Recipiente inferido: {recipiente_inferido}")
                break
        
        for produto in produtos_db:
            score = 0
            razoes = []
            descricao = produto.descricao_produto.upper()
            
            # === 1. DETECÇÃO DE MARCA (PESO ALTO) ===
            for marca_principal, aliases in marcas_aliases.items():
                # Verifica se a marca está no OCR (qualquer alias)
                marca_no_ocr = any(alias in texto_ocr_str for alias in aliases)
                # Verifica se a marca está na descrição do produto
                marca_no_produto = any(alias in descricao for alias in aliases)
                
                if marca_no_ocr and marca_no_produto:
                    score += 35  # Peso alto para match de marca
                    razoes.append(f"Marca: {marca_principal}")
                    break
            
            # === 2. DETECÇÃO DE RECIPIENTE/EMBALAGEM (PESO ALTO) ===
            # Usa recipiente inferido pelo volume OU a forma detectada pela visão
            recipiente_usado = recipiente_inferido if recipiente_inferido else forma
            if recipiente_usado:
                aliases_forma = recipientes_aliases.get(recipiente_usado, [])
                for alias in aliases_forma:
                    if alias in descricao:
                        score += 25  # Peso alto para recipiente
                        if recipiente_usado == 'latao':
                            razoes.append(f"Recipiente: LATÃO (473ml)")
                        elif recipiente_usado == 'long neck':
                            razoes.append(f"Recipiente: LONG NECK (330ml)")
                        elif recipiente_usado == 'pet':
                            razoes.append(f"Recipiente: PET")
                        else:
                            razoes.append(f"Recipiente: {recipiente_usado.upper()}")
                        break
            
            # === 3. DETECÇÃO DE VOLUME (PESO MÉDIO-ALTO) ===
            for vol in volumes_conhecidos:
                vol_variantes = [vol, vol.replace('ML', ' ML'), vol.replace('L', ' L'), vol.replace('LT', ' LT')]
                vol_no_ocr = any(v in texto_ocr_str for v in vol_variantes)
                vol_no_produto = any(v in descricao for v in vol_variantes)
                
                if vol_no_ocr and vol_no_produto:
                    score += 30  # Aumentado - volume é muito importante
                    razoes.append(f"Volume: {vol}")
                    break
            
            # === 4. DETECÇÃO DE TIPO DE CERVEJA (PESO MÉDIO) ===
            for tipo_principal, aliases in tipos_cerveja_aliases.items():
                tipo_no_ocr = any(alias in texto_ocr_str for alias in aliases)
                tipo_no_produto = any(alias in descricao for alias in aliases)
                
                if tipo_no_ocr and tipo_no_produto:
                    score += 20
                    razoes.append(f"Tipo Cerveja: {tipo_principal}")
                    break
            
            # === 5. DETECÇÃO DE TIPO DE REFRIGERANTE (PESO MÉDIO) ===
            for tipo_principal, aliases in tipos_refri_aliases.items():
                tipo_no_ocr = any(alias in texto_ocr_str for alias in aliases)
                tipo_no_produto = any(alias in descricao for alias in aliases)
                
                if tipo_no_ocr and tipo_no_produto:
                    score += 20
                    razoes.append(f"Tipo Refri: {tipo_principal}")
                    break
            
            # === 6. PALAVRAS OCR INDIVIDUAIS (PESO MÉDIO) ===
            palavras_match = 0
            for palavra in texto_ocr:
                if len(palavra) >= 3:  # Ignorar palavras muito curtas
                    # Match exato
                    if palavra in descricao:
                        palavras_match += 1
                        score += 8
                    # Match parcial (palavra contida na descrição)
                    elif any(palavra in p or p in palavra for p in descricao.split()):
                        palavras_match += 0.5
                        score += 4
            
            if palavras_match > 0:
                razoes.append(f"Palavras: {int(palavras_match)} matches")
            
            # === 7. SIMILARIDADE GERAL (FALLBACK) ===
            if score < 20:  # Se não teve bons matches, tentar similaridade geral
                similaridade = calcular_similaridade(texto_ocr_str, descricao)
                if similaridade > 30:
                    score += similaridade * 0.3
                    razoes.append(f"Similaridade: {similaridade:.0f}%")
            
            # === 8. BONUS: Long Neck (recipiente específico) ===
            if ('LONG' in texto_ocr_str or 'NECK' in texto_ocr_str) and ('LONG' in descricao or 'NECK' in descricao):
                score += 10
                if 'LONG NECK' not in ' '.join(razoes):
                    razoes.append("Recipiente: LONG NECK")
            
            # Atualizar melhor match
            if score > melhor_score:
                melhor_score = score
                melhor_match = produto.id
                melhor_razao = " | ".join(razoes[:5]) if razoes else "Baixa correspondência"
        
        # Normalizar confiança (0-100%)
        # Score máximo teórico: 35 (marca) + 25 (recipiente) + 30 (volume) + 20 (tipo cerveja) + 20 (tipo refri) + 24 (palavras) = ~154
        confianca = min(95, (melhor_score / 100) * 100) if melhor_score > 0 else 0
        
        print(f"🎯 Melhor match: score={melhor_score}, confianca={confianca:.1f}%, razao={melhor_razao}")
        
        return (melhor_match, round(confianca, 2), melhor_razao)
        
    except Exception as e:
        print(f"Erro ao sugerir produto: {e}")
        import traceback
        traceback.print_exc()
        return (None, 0, "Erro na análise")


@csrf_exempt
@login_required
def detectar_produtos_api(request):
    """API para detectar produtos automaticamente em imagens usando YOLO + OCR + Análise de Forma"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    if 'image' not in request.FILES:
        return JsonResponse({'error': 'Nenhuma imagem enviada'}, status=400)
    
    try:
        imagem = request.FILES['image']
        
        # Converter para numpy array
        img_bytes = np.frombuffer(imagem.read(), np.uint8)
        img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
        
        if img is None:
            return JsonResponse({'error': 'Erro ao decodificar imagem'}, status=400)
        
        height, width = img.shape[:2]
        
        # Detectar objetos com YOLO
        model = get_yolo_model()
        results = model(img, conf=0.25, iou=0.45)
        
        # Carregar produtos do banco para sugestão
        produtos_db = list(ProdutoMae.objects.all())
        
        # Extrair bboxes com análise inteligente
        bboxes = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Converter para formato normalizado (x_center, y_center, width, height)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # Extrair região do bbox
                bbox_img = img[y1:y2, x1:x2]
                
                # 🔥 PRIORIDADE 1: Detectar código de barras
                codigo_barras, tipo_barcode = detectar_codigo_barras(bbox_img)
                
                # Análise de forma
                forma = classificar_forma_produto(bbox_img)
                
                # OCR na região
                texto_ocr = extrair_texto_ocr(bbox_img)
                
                # Sugestão de produto (com código de barras = 99.99% confiança)
                produto_sugerido_id, confianca_sugestao, razao = sugerir_produto_ia(
                    texto_ocr, forma, produtos_db, codigo_barras=codigo_barras
                )
                
                # Calcular centro e dimensões normalizadas
                x_center = ((x1 + x2) / 2) / width
                y_center = ((y1 + y2) / 2) / height
                bbox_width = (x2 - x1) / width
                bbox_height = (y2 - y1) / height
                
                confidence = float(box.conf[0].cpu().numpy())
                
                bbox_data = {
                    'x': float(x_center),
                    'y': float(y_center),
                    'width': float(bbox_width),
                    'height': float(bbox_height),
                    'confidence': confidence,
                    'codigo_barras': codigo_barras,  # 🔥 NOVO: Código de barras detectado
                    'tipo_barcode': tipo_barcode,    # Tipo (EAN13, CODE128, etc.)
                    'forma': forma,
                    'ocr_texto': texto_ocr,
                    'produto_sugerido_id': produto_sugerido_id,
                    'confianca_sugestao': confianca_sugestao,
                    'razao_sugestao': razao
                }
                
                bboxes.append(bbox_data)
        
        return JsonResponse({
            'success': True,
            'bboxes': bboxes,
            'count': len(bboxes),
            'analise_completa': True
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def revisar_desconhecidos(request):
    """Interface para revisar imagens sem produto associado correto COM BBOX"""
    
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado. Apenas administradores.')
        return redirect('home')
    
    # Buscar imagens problemáticas
    imagens = ImagemProdutoPendente.objects.filter(
        Q(produto__descricao_produto__icontains='DESCONHECIDO') |
        Q(produto__descricao_produto__icontains='FAMILIA_HEINEKEN_MANUAL')
    ).filter(status='pendente').select_related('produto', 'enviado_por')[:10]  # Limitar a 10
    
    # Preparar dados para JavaScript
    imagens_json = []
    for img in imagens:
        imagens_json.append({
            'id': img.id,
            'url': img.imagem.url,
            'filename': img.imagem.name.split('/')[-1],
            'produto_atual': img.produto.descricao_produto
        })
    
    # Preparar produtos para select
    produtos = ProdutoMae.objects.all().order_by('descricao_produto')
    produtos_json = [{'id': p.id, 'nome': p.descricao_produto} for p in produtos]
    
    context = {
        'imagens_json': json.dumps(imagens_json),
        'produtos_json': json.dumps(produtos_json),
        'total': imagens.count()
    }
    
    return render(request, 'verifik/revisar_com_bbox.html', context)


@csrf_exempt
@login_required
def aprovar_bbox_api(request):
    """API para aprovar um bbox específico e salvar no dataset"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        imagem_id = data.get('imagem_id')
        produto_id = data.get('produto_id')
        bbox_data = data.get('bbox_data')
        
        if not all([imagem_id, produto_id, bbox_data]):
            return JsonResponse({'error': 'Dados incompletos'}, status=400)
        
        imagem = get_object_or_404(ImagemProdutoPendente, id=imagem_id)
        produto = get_object_or_404(ProdutoMae, id=produto_id)
        
        # Recortar bbox da imagem
        img = Image.open(imagem.imagem.path)
        img_width, img_height = img.size
        
        # Converter coordenadas normalizadas para pixels
        x_center = bbox_data['x'] * img_width
        y_center = bbox_data['y'] * img_height
        bbox_width = bbox_data['width'] * img_width
        bbox_height = bbox_data['height'] * img_height
        
        x1 = int(x_center - bbox_width / 2)
        y1 = int(y_center - bbox_height / 2)
        x2 = int(x_center + bbox_width / 2)
        y2 = int(y_center + bbox_height / 2)
        
        # Recortar
        cropped = img.crop((x1, y1, x2, y2))
        
        # Salvar no dataset
        base_path = Path('assets/dataset/train') / produto.descricao_produto.replace(' ', '_')
        base_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S_%f')
        novo_nome = f"{produto.descricao_produto.replace(' ', '_')}_{timestamp}.jpg"
        destino = base_path / novo_nome
        
        cropped.save(destino, 'JPEG', quality=95)
        
        # Criar nova entrada no banco (um produto por bbox)
        nova_imagem = ImagemProdutoPendente.objects.create(
            produto=produto,
            imagem=imagem.imagem,  # Mesma imagem original
            enviado_por=imagem.enviado_por,
            lote=imagem.lote,
            status='aprovada',
            aprovado_por=request.user,
            data_aprovacao=timezone.now(),
            bbox_data=json.dumps([bbox_data])  # Salvar bbox usado
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Bbox salvo no dataset: {novo_nome}',
            'nova_imagem_id': nova_imagem.id
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def reclassificar_imagem(request, imagem_id):
    """Reclassifica uma imagem para um novo produto"""
    
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    imagem = get_object_or_404(ImagemProdutoPendente, id=imagem_id)
    
    if request.method == 'POST':
        novo_produto_id = request.POST.get('produto_id')
        
        if novo_produto_id:
            novo_produto = get_object_or_404(ProdutoMae, id=novo_produto_id)
            imagem.produto = novo_produto
            imagem.save()
            
            messages.success(request, f'✅ Imagem reclassificada para "{novo_produto.descricao_produto}"!')
        else:
            messages.error(request, 'Selecione um produto')
    
    return redirect('revisar_desconhecidos')


@login_required
def processar_automatico(request):
    """Interface para processar imagens automaticamente com IA"""
    
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado. Apenas administradores.')
        return redirect('home')
    
    # Buscar TODAS as imagens pendentes (sem filtro de produto específico)
    total = ImagemProdutoPendente.objects.filter(status='pendente').count()
    
    # Preparar produtos para select
    produtos = ProdutoMae.objects.all().order_by('descricao_produto')
    produtos_json = [{'id': p.id, 'nome': p.descricao_produto} for p in produtos]
    
    context = {
        'total_pendentes': total,
        'produtos_json': json.dumps(produtos_json),
    }
    
    return render(request, 'verifik/processar_automatico.html', context)


@csrf_exempt
@login_required
def processar_automatico_api(request):
    """API para processar imagens automaticamente com IA"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        limite = data.get('limite', 10)
        auto_folder = data.get('auto_folder', True)
        pasta_files = data.get('pasta_files', [])

        resultados = []
        produtos_db = list(ProdutoMae.objects.all())
        produtos_ids = set(p.id for p in produtos_db)

        imagens = []
        # Se pasta_files foi enviado, processa arquivos locais
        if not auto_folder and pasta_files:
            # Pasta base: pode ser configurada ou usar padrão
            pasta_base = 'media/produtos/pendentes/'
            for rel_path in pasta_files[:limite]:
                abs_path = os.path.join(pasta_base, rel_path)
                if not os.path.exists(abs_path):
                    continue
                imagens.append({'path': abs_path, 'id': rel_path, 'url': '', 'produto': 'DESCONHECIDO'})
        else:
            # Busca TODAS as pendentes do banco (sem filtro de produto específico)
            pendentes = ImagemProdutoPendente.objects.filter(status='pendente')[:limite]
            for imagem in pendentes:
                produto_nome = imagem.produto.descricao_produto if imagem.produto else 'SEM PRODUTO'
                imagens.append({'path': imagem.imagem.path, 'id': imagem.id, 'url': imagem.imagem.url, 'produto': produto_nome})

        for imagem in imagens:
            try:
                img = cv2.imread(imagem['path'])
                if img is None:
                    continue
                height, width = img.shape[:2]
                # YOLO - Detectar produtos
                model = get_yolo_model()
                results = model(img, conf=0.25, iou=0.45)
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        conf = float(box.conf[0].cpu().numpy())
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        # Cortar bbox/frame
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        bbox_img = img[y1:y2, x1:x2]
                        # Detectar código de barras
                        codigo_barras, tipo_barcode = detectar_codigo_barras(bbox_img)
                        # Classificar forma
                        forma = classificar_forma_produto(bbox_img)
                        # OCR
                        texto_ocr = extrair_texto_ocr(bbox_img)
                        # Sugestão (sempre do banco)
                        produto_id, confianca, razao = sugerir_produto_ia(
                            texto_ocr, forma, produtos_db, codigo_barras=codigo_barras
                        )
                        # Garantir que só produtos do banco sejam sugeridos
                        if produto_id not in produtos_ids:
                            produto_id = ''
                            razao += ' [Produto não cadastrado]'
                        # Determinar método de detecção
                        metodo_deteccao = ''
                        if codigo_barras:
                            metodo_deteccao = 'Código de Barras'
                        else:
                            metodo_deteccao = 'YOLO'
                            if texto_ocr and any([t for t in texto_ocr if t.strip()]):
                                metodo_deteccao += ' + OCR'
                        # Converter bbox para normalizado
                        x_center = ((x1 + x2) / 2) / width
                        y_center = ((y1 + y2) / 2) / height
                        bbox_width = (x2 - x1) / width
                        bbox_height = (y2 - y1) / height
                        resultados.append({
                            'imagem_id': imagem['id'],
                            'imagem_url': imagem['url'],
                            'produto_atual': imagem['produto'],
                            'produto_sugerido_id': produto_id,
                            'confianca': confianca,
                            'razao': razao,
                            'codigo_barras': codigo_barras,
                            'tipo_barcode': tipo_barcode,
                            'forma': forma,
                            'ocr_texto': texto_ocr,
                            'metodo_deteccao': metodo_deteccao,
                            'bbox': {
                                'x': float(x_center),
                                'y': float(y_center),
                                'width': float(bbox_width),
                                'height': float(bbox_height)
                            }
                        })
            except Exception as e:
                print(f"Erro ao processar imagem {imagem['id']}: {e}")
                continue

        return JsonResponse({
            'success': True,
            'resultados': resultados,
            'total': len(resultados)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
def aprovar_processamento(request):
    """API para aprovar sugestão de produto"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        imagem_id = data.get('imagem_id')
        produto_id = data.get('produto_id')
        
        if not all([imagem_id, produto_id]):
            return JsonResponse({'error': 'Dados incompletos'}, status=400)
        
        imagem = get_object_or_404(ImagemProdutoPendente, id=imagem_id)
        produto = get_object_or_404(ProdutoMae, id=produto_id)

        # Receber bbox e método de detecção
        bbox = data.get('bbox')
        metodo = data.get('metodo_deteccao', '')
        if bbox:
            imagem.bbox_data = json.dumps(bbox)
        if metodo:
            imagem.metodo_deteccao = metodo

        # Atualizar imagem
        imagem.produto = produto
        imagem.status = 'aprovada'
        imagem.aprovado_por = request.user
        imagem.data_aprovacao = timezone.now()
        imagem.save()

        return JsonResponse({
            'success': True,
            'message': f'Produto aprovado: {produto.descricao_produto}'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

