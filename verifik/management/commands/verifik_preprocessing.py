from django.core.management.base import BaseCommand
from pathlib import Path
import cv2
import numpy as np
import os
from datetime import datetime


class Command(BaseCommand):
    help = 'Sistema VerifiK - Pré-processamento com Remoção de Fundo Avançada'

    def add_arguments(self, parser):
        parser.add_argument('--imagem', type=str, required=True,
                          help='Caminho para imagem a processar')
        parser.add_argument('--metodo', type=str, default='todos',
                          choices=['grabcut', 'watershed', 'mog2', 'u2net', 'todos'],
                          help='Método de remoção de fundo (padrão: todos)')
        parser.add_argument('--save-steps', action='store_true',
                          help='Salvar passos intermediários')

    def handle(self, *args, **options):
        imagem_path = options['imagem']
        metodo = options['metodo']
        save_steps = options['save_steps']

        self.stdout.write('=' * 100)
        self.stdout.write('🎨 SISTEMA VERIFIK - PRÉ-PROCESSAMENTO COM REMOÇÃO DE FUNDO')
        self.stdout.write('=' * 100)
        
        self.stdout.write(f'\n📊 Configuração:')
        self.stdout.write(f'   Imagem: {Path(imagem_path).name}')
        self.stdout.write(f'   Método: {metodo.upper()}')

        # Verificar se imagem existe
        if not Path(imagem_path).exists():
            self.stdout.write(self.style.ERROR(f'✗ Imagem não encontrada: {imagem_path}'))
            return

        try:
            # Criar pasta de resultados
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = Path(f'verifik_preprocessing_{timestamp}')
            output_dir.mkdir(exist_ok=True)
            
            self.stdout.write(f'\n📁 Pasta de resultados: {output_dir.absolute()}')

            # Carregar imagem original
            img_original = cv2.imread(imagem_path)
            if img_original is None:
                self.stdout.write(self.style.ERROR('✗ Erro ao carregar imagem'))
                return
                
            altura, largura = img_original.shape[:2]
            self.stdout.write(f'✓ Imagem carregada: {largura}x{altura}')
            
            # Salvar original
            original_path = output_dir / '0_original.jpg'
            cv2.imwrite(str(original_path), img_original)

            # ETAPA 1: PRÉ-PROCESSAMENTO BÁSICO
            img_preprocessada = self.preprocessamento_basico(img_original, output_dir, save_steps)
            
            # ETAPA 2: REMOÇÃO DE FUNDO
            if metodo == 'todos':
                resultados = self.aplicar_todos_metodos(img_preprocessada, output_dir, save_steps)
            else:
                resultado = self.aplicar_metodo_especifico(img_preprocessada, metodo, output_dir, save_steps)
                resultados = {metodo: resultado}
            
            # ETAPA 3: OTIMIZAÇÃO FINAL
            melhor_resultado = self.selecionar_melhor_resultado(resultados, output_dir, save_steps)
            
            # ETAPA 4: RESULTADO FINAL
            self.gerar_resultado_final(melhor_resultado, output_dir)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro: {str(e)}'))
            import traceback
            traceback.print_exc()

    def preprocessamento_basico(self, img, output_dir, save_steps):
        """ETAPA 1: Pré-processamento básico da imagem"""
        self.stdout.write(f'\n🔧 ETAPA 1: PRÉ-PROCESSAMENTO BÁSICO')
        
        # 1. Redução de ruído (versão rápida)
        img_denoised = cv2.bilateralFilter(img, 5, 50, 50)
        self.stdout.write('   ✓ Redução de ruído aplicada (bilateral filter)')
        
        # 2. Equalização de histograma adaptativa
        lab = cv2.cvtColor(img_denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        img_enhanced = cv2.merge([l, a, b])
        img_enhanced = cv2.cvtColor(img_enhanced, cv2.COLOR_LAB2BGR)
        self.stdout.write('   ✓ Equalização adaptativa aplicada')
        
        # 3. Sharpening (aguçamento)
        kernel_sharp = np.array([[-1,-1,-1],
                               [-1, 9,-1],
                               [-1,-1,-1]])
        img_sharp = cv2.filter2D(img_enhanced, -1, kernel_sharp)
        self.stdout.write('   ✓ Sharpening aplicado')
        
        # 4. Ajuste de saturação para melhorar cores dos rótulos
        hsv = cv2.cvtColor(img_sharp, cv2.COLOR_BGR2HSV)
        hsv[:,:,1] = cv2.multiply(hsv[:,:,1], 1.2)  # Aumentar saturação em 20%
        img_resultado = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        self.stdout.write('   ✓ Saturação ajustada')
        
        if save_steps:
            preprocessed_path = output_dir / '1_preprocessamento_basico.jpg'
            cv2.imwrite(str(preprocessed_path), img_resultado)
            self.stdout.write(f'   💾 Salvo: {preprocessed_path.name}')
        
        return img_resultado

    def aplicar_todos_metodos(self, img, output_dir, save_steps):
        """ETAPA 2: Aplicar todos os métodos de remoção de fundo"""
        self.stdout.write(f'\n🎭 ETAPA 2: REMOÇÃO DE FUNDO - TODOS OS MÉTODOS')
        
        resultados = {}
        
        # Método 1: GrabCut
        try:
            self.stdout.write(f'\n   🔸 Método 1: GrabCut')
            resultado_grabcut = self.remover_fundo_grabcut(img)
            resultados['grabcut'] = resultado_grabcut
            if save_steps:
                grabcut_path = output_dir / '2a_grabcut.jpg'
                cv2.imwrite(str(grabcut_path), resultado_grabcut)
                self.stdout.write(f'     💾 Salvo: {grabcut_path.name}')
            self.stdout.write('     ✓ GrabCut concluído')
        except Exception as e:
            self.stdout.write(f'     ✗ GrabCut falhou: {str(e)}')
        
        # Método 2: Watershed
        try:
            self.stdout.write(f'\n   🔸 Método 2: Watershed')
            resultado_watershed = self.remover_fundo_watershed(img)
            resultados['watershed'] = resultado_watershed
            if save_steps:
                watershed_path = output_dir / '2b_watershed.jpg'
                cv2.imwrite(str(watershed_path), resultado_watershed)
                self.stdout.write(f'     💾 Salvo: {watershed_path.name}')
            self.stdout.write('     ✓ Watershed concluído')
        except Exception as e:
            self.stdout.write(f'     ✗ Watershed falhou: {str(e)}')
        
        # Método 3: MOG2 Background Subtractor
        try:
            self.stdout.write(f'\n   🔸 Método 3: MOG2 Background Subtractor')
            resultado_mog2 = self.remover_fundo_mog2(img)
            resultados['mog2'] = resultado_mog2
            if save_steps:
                mog2_path = output_dir / '2c_mog2.jpg'
                cv2.imwrite(str(mog2_path), resultado_mog2)
                self.stdout.write(f'     💾 Salvo: {mog2_path.name}')
            self.stdout.write('     ✓ MOG2 concluído')
        except Exception as e:
            self.stdout.write(f'     ✗ MOG2 falhou: {str(e)}')
        
        # Método 4: Segmentação por cor (produtos coloridos)
        try:
            self.stdout.write(f'\n   🔸 Método 4: Segmentação por Cor')
            resultado_cor = self.remover_fundo_por_cor(img)
            resultados['cor'] = resultado_cor
            if save_steps:
                cor_path = output_dir / '2d_segmentacao_cor.jpg'
                cv2.imwrite(str(cor_path), resultado_cor)
                self.stdout.write(f'     💾 Salvo: {cor_path.name}')
            self.stdout.write('     ✓ Segmentação por cor concluída')
        except Exception as e:
            self.stdout.write(f'     ✗ Segmentação por cor falhou: {str(e)}')
        
        # Método 5: Contorno inteligente
        try:
            self.stdout.write(f'\n   🔸 Método 5: Contorno Inteligente')
            resultado_contorno = self.remover_fundo_contorno(img)
            resultados['contorno'] = resultado_contorno
            if save_steps:
                contorno_path = output_dir / '2e_contorno_inteligente.jpg'
                cv2.imwrite(str(contorno_path), resultado_contorno)
                self.stdout.write(f'     💾 Salvo: {contorno_path.name}')
            self.stdout.write('     ✓ Contorno inteligente concluído')
        except Exception as e:
            self.stdout.write(f'     ✗ Contorno inteligente falhou: {str(e)}')
        
        return resultados

    def aplicar_metodo_especifico(self, img, metodo, output_dir, save_steps):
        """Aplicar método específico de remoção de fundo"""
        self.stdout.write(f'\n🎭 ETAPA 2: REMOÇÃO DE FUNDO - {metodo.upper()}')
        
        if metodo == 'grabcut':
            return self.remover_fundo_grabcut(img)
        elif metodo == 'watershed':
            return self.remover_fundo_watershed(img)
        elif metodo == 'mog2':
            return self.remover_fundo_mog2(img)
        else:
            return img

    def remover_fundo_grabcut(self, img):
        """Método 1: GrabCut - Segmentação interativa"""
        altura, largura = img.shape[:2]
        
        # Criar máscara inicial (assumir que o centro contém o objeto)
        mask = np.zeros((altura, largura), np.uint8)
        
        # Definir retângulo inicial (80% do centro da imagem)
        margem_x = int(largura * 0.1)
        margem_y = int(altura * 0.1)
        rect = (margem_x, margem_y, largura - 2*margem_x, altura - 2*margem_y)
        
        # Criar modelos de fundo e objeto
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        
        # Executar GrabCut
        cv2.grabCut(img, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
        
        # Criar máscara binária (manter apenas foreground definido e provável)
        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
        
        # Aplicar máscara
        resultado = img * mask2[:, :, np.newaxis]
        
        return resultado

    def remover_fundo_watershed(self, img):
        """Método 2: Watershed - Segmentação baseada em marcadores"""
        # Converter para escala de cinza
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Threshold para separar fundo dos objetos
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Operações morfológicas para limpar
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
        
        # Dilatação para ter certeza do fundo
        sure_bg = cv2.dilate(opening, kernel, iterations=3)
        
        # Transform de distância
        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        
        # Threshold na transform de distância para obter foreground
        _, sure_fg = cv2.threshold(dist_transform, 0.7 * dist_transform.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)
        
        # Região desconhecida
        unknown = cv2.subtract(sure_bg, sure_fg)
        
        # Criar marcadores
        _, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0
        
        # Aplicar Watershed
        markers = cv2.watershed(img, markers)
        
        # Criar máscara
        mask = np.zeros(gray.shape, dtype=np.uint8)
        mask[markers > 1] = 255
        
        # Aplicar máscara
        resultado = cv2.bitwise_and(img, img, mask=mask)
        
        return resultado

    def remover_fundo_mog2(self, img):
        """Método 3: MOG2 Background Subtractor"""
        # Criar background subtractor
        backSub = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
        
        # Simular sequência de frames (usar a mesma imagem múltiplas vezes)
        for i in range(10):
            # Adicionar pequenas variações para simular movimento
            noise = np.random.randint(-5, 6, img.shape, dtype=np.int16)
            img_variant = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            mask = backSub.apply(img_variant)
        
        # Obter máscara final
        mask_final = backSub.apply(img)
        
        # Operações morfológicas para limpar máscara
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask_clean = cv2.morphologyEx(mask_final, cv2.MORPH_OPEN, kernel)
        mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_CLOSE, kernel)
        
        # Aplicar máscara
        resultado = cv2.bitwise_and(img, img, mask=mask_clean)
        
        return resultado

    def remover_fundo_por_cor(self, img):
        """Método 4: Segmentação por cor (especial para produtos coloridos)"""
        # Converter para HSV para melhor separação de cores
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Definir ranges de cores comuns em fundos (branco, cinza, preto)
        # Fundo branco/claro
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        mask_white = cv2.inRange(hsv, lower_white, upper_white)
        
        # Fundo cinza
        lower_gray = np.array([0, 0, 50])
        upper_gray = np.array([180, 30, 200])
        mask_gray = cv2.inRange(hsv, lower_gray, upper_gray)
        
        # Combinar máscaras de fundo
        mask_background = cv2.bitwise_or(mask_white, mask_gray)
        
        # Inverter máscara para pegar objetos
        mask_objects = cv2.bitwise_not(mask_background)
        
        # Operações morfológicas para limpar
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask_objects = cv2.morphologyEx(mask_objects, cv2.MORPH_CLOSE, kernel)
        mask_objects = cv2.morphologyEx(mask_objects, cv2.MORPH_OPEN, kernel)
        
        # Aplicar máscara
        resultado = cv2.bitwise_and(img, img, mask=mask_objects)
        
        return resultado

    def remover_fundo_contorno(self, img):
        """Método 5: Contorno inteligente baseado em gradientes"""
        # Converter para escala de cinza
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Aplicar filtro bilateral para preservar bordas
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Detectar bordas com Canny
        edges = cv2.Canny(bilateral, 50, 150)
        
        # Dilatação para conectar bordas próximas
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges_dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(edges_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtrar contornos por área (manter apenas contornos grandes)
        altura, largura = img.shape[:2]
        area_minima = (altura * largura) * 0.01  # Mínimo 1% da imagem
        
        mask = np.zeros(gray.shape, dtype=np.uint8)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > area_minima:
                # Preencher contorno
                cv2.fillPoly(mask, [contour], 255)
        
        # Operações morfológicas finais
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)
        
        # Aplicar máscara
        resultado = cv2.bitwise_and(img, img, mask=mask)
        
        return resultado

    def selecionar_melhor_resultado(self, resultados, output_dir, save_steps):
        """ETAPA 3: Selecionar o melhor resultado baseado em métricas"""
        self.stdout.write(f'\n🏆 ETAPA 3: SELEÇÃO DO MELHOR RESULTADO')
        
        if not resultados:
            self.stdout.write('   ⚠️  Nenhum resultado disponível')
            return None
        
        melhor_score = 0
        melhor_resultado = None
        melhor_metodo = None
        
        for metodo, resultado in resultados.items():
            score = self.avaliar_qualidade_resultado(resultado)
            
            self.stdout.write(f'   📊 {metodo.upper()}: Score = {score:.3f}')
            
            if score > melhor_score:
                melhor_score = score
                melhor_resultado = resultado
                melhor_metodo = metodo
        
        self.stdout.write(f'\n   🥇 VENCEDOR: {melhor_metodo.upper()} (Score: {melhor_score:.3f})')
        
        if save_steps:
            melhor_path = output_dir / f'3_melhor_resultado_{melhor_metodo}.jpg'
            cv2.imwrite(str(melhor_path), melhor_resultado)
            self.stdout.write(f'   💾 Melhor resultado salvo: {melhor_path.name}')
        
        return {
            'imagem': melhor_resultado,
            'metodo': melhor_metodo,
            'score': melhor_score
        }

    def avaliar_qualidade_resultado(self, img):
        """Avaliar qualidade do resultado baseado em métricas"""
        # Converter para escala de cinza
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Métrica 1: Variância (maior = melhor contraste)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        score_variance = min(variance / 1000, 1.0)  # Normalizar
        
        # Métrica 2: Porcentagem de pixels não-pretos (maior = melhor preservação)
        non_black_pixels = np.sum(gray > 10)
        total_pixels = gray.shape[0] * gray.shape[1]
        score_preservation = non_black_pixels / total_pixels
        
        # Métrica 3: Detecção de bordas (maior = melhor definição)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / total_pixels
        score_edges = min(edge_density * 10, 1.0)  # Normalizar
        
        # Score final (média ponderada)
        score_final = (score_variance * 0.4 + score_preservation * 0.4 + score_edges * 0.2)
        
        return score_final

    def gerar_resultado_final(self, melhor_resultado, output_dir):
        """ETAPA 4: Gerar resultado final otimizado"""
        self.stdout.write(f'\n🎨 ETAPA 4: RESULTADO FINAL OTIMIZADO')
        
        if melhor_resultado is None:
            self.stdout.write('   ⚠️  Nenhum resultado para otimizar')
            return
        
        img = melhor_resultado['imagem']
        metodo = melhor_resultado['metodo']
        score = melhor_resultado['score']
        
        # Aplicar otimizações finais
        img_otimizada = self.aplicar_otimizacoes_finais(img)
        
        # Salvar resultado final
        resultado_path = output_dir / '4_resultado_final_preprocessado.jpg'
        cv2.imwrite(str(resultado_path), img_otimizada)
        
        # Criar comparação antes/depois
        self.criar_comparacao_antes_depois(output_dir)
        
        # Abrir resultado
        os.startfile(str(resultado_path))
        
        self.stdout.write(f'\n📊 RESUMO FINAL:')
        self.stdout.write(f'   ✓ Melhor método: {metodo.upper()}')
        self.stdout.write(f'   ✓ Score de qualidade: {score:.3f}')
        self.stdout.write(f'   ✓ Otimizações aplicadas')
        
        self.stdout.write(f'\n💾 Arquivo final: {resultado_path.name}')
        self.stdout.write(f'📁 Todos os arquivos em: {output_dir.absolute()}')
        self.stdout.write(f'\n👁️  RESULTADO FINAL ABERTO!')

    def aplicar_otimizacoes_finais(self, img):
        """Aplicar otimizações finais na imagem"""
        # 1. Remoção de ruído final
        img_final = cv2.bilateralFilter(img, 9, 75, 75)
        
        # 2. Ajuste de contraste automático
        gray = cv2.cvtColor(img_final, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        gray_enhanced = clahe.apply(gray)
        
        # Aplicar enhancement apenas nos canais de cor
        lab = cv2.cvtColor(img_final, cv2.COLOR_BGR2LAB)
        lab[:,:,0] = gray_enhanced
        img_final = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # 3. Sharpening suave final
        kernel_sharp = np.array([[0,-1,0],
                               [-1,5,-1],
                               [0,-1,0]])
        img_final = cv2.filter2D(img_final, -1, kernel_sharp)
        
        return img_final

    def criar_comparacao_antes_depois(self, output_dir):
        """Criar imagem de comparação antes/depois"""
        try:
            original_path = output_dir / '0_original.jpg'
            final_path = output_dir / '4_resultado_final_preprocessado.jpg'
            
            if original_path.exists() and final_path.exists():
                img_original = cv2.imread(str(original_path))
                img_final = cv2.imread(str(final_path))
                
                # Redimensionar para mesmo tamanho se necessário
                h_orig, w_orig = img_original.shape[:2]
                img_final = cv2.resize(img_final, (w_orig, h_orig))
                
                # Criar imagem lado a lado
                comparacao = np.hstack((img_original, img_final))
                
                # Adicionar texto
                cv2.putText(comparacao, 'ANTES', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
                cv2.putText(comparacao, 'DEPOIS', (w_orig + 50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
                
                comparacao_path = output_dir / '5_comparacao_antes_depois.jpg'
                cv2.imwrite(str(comparacao_path), comparacao)
                
                self.stdout.write(f'   💾 Comparação salva: {comparacao_path.name}')
                
        except Exception as e:
            self.stdout.write(f'   ⚠️  Erro ao criar comparação: {str(e)}')