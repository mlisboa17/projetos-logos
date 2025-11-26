"""
Relatório de Configurações de Paths do Sistema VerifiK
Gerado em: 26/11/2025
"""

# ============================================================
# 📊 RESUMO DO SISTEMA
# ============================================================

Total de Imagens no Banco: 398 imagens
Produtos com Imagens: 10 produtos
Produtos sem Imagens: 166 produtos

# ============================================================
# 📁 ESTRUTURA DE DIRETÓRIOS
# ============================================================

## Imagens em Produção (media/)
- Total: 837 arquivos de imagem
- Usado para: Armazenamento de imagens enviadas pelos usuários

## Datasets de Treino
- verifik/dataset_treino/: 385 imagens
  → Datasets temporários gerados para cada treino
  → Estrutura: 
    - verifik/dataset_treino/{timestamp}/images/train/
    - verifik/dataset_treino/{timestamp}/labels/train/
  
- dataset_corrigido/: 6 imagens
  → Dataset com anotações corrigidas manualmente

# ============================================================
# ⚙️ CONFIGURAÇÕES POR ARQUIVO
# ============================================================

## 1. treinar_modelo_yolo.py (Treinamento Principal)
   Descrição: Script principal de treinamento do modelo YOLO
   
   Paths Configurados:
   - Dataset: BASE_DIR / 'verifik' / 'dataset_yolo'
   - Checkpoint: BASE_DIR / 'verifik' / 'runs' / 'treino_verifik' / 'weights' / 'last.pt'
   - Modelo Final: BASE_DIR / 'verifik' / 'verifik_yolov8.pt'
   
   Funcionalidade:
   - Busca imagens do banco de dados (ImagemProduto)
   - Cria dataset YOLO com train/val split
   - Treina modelo a partir de checkpoint ou do zero
   - Salva melhor modelo como verifik_yolov8.pt

## 2. treinar_simples.py (Treinamento Simplificado)
   Descrição: Versão simplificada do treinamento
   
   Paths Configurados:
   - Dataset: Path('verifik/dataset_treino') / {timestamp}
   - Images: dataset_path / 'images' / 'train'
   - Labels: dataset_path / 'labels' / 'train'
   
   Funcionalidade:
   - Cria dataset timestamped (ex: verifik/dataset_treino/20251126_143000/)
   - Sem split de validação
   - Mais rápido para testes

## 3. treinar_incremental.py (Treinamento Incremental)
   Descrição: Adiciona novos produtos ao modelo existente
   
   Paths Configurados:
   - Dataset: verifik/dataset_treino_incremental/{timestamp}
   - Checkpoint: Vários locais possíveis (prioridade):
     1. verifik/verifik_yolov8.pt
     2. verifik/runs/treino_verifik/weights/last.pt
     3. verifik/runs/treino_verifik/weights/best.pt
   
   Funcionalidade:
   - Continua treinamento do modelo existente
   - Aplica data augmentation (6 variações por imagem)
   - Ideal para adicionar novos produtos sem retreinar tudo

## 4. testar_deteccao.py (Teste de Detecção)
   Descrição: Testa modelo em imagens
   
   Paths Configurados:
   - Resultados: Path("resultados_deteccao/teste")
   - Modelo: Busca automaticamente em:
     1. verifik/verifik_yolov8.pt
     2. verifik/runs/treino_verifik/weights/best.pt
   
   Funcionalidade:
   - Detecta produtos em imagens
   - Salva resultados com bounding boxes
   - Mostra confiança das detecções

## 5. detector_simples.py (Detector com Correções)
   Descrição: Detector interativo com correção manual
   
   Paths Configurados:
   - Dataset Corrigido: Path("dataset_corrigido")
     - Images: dataset_corrigido/images/
     - Labels: dataset_corrigido/labels/
     - Classes: dataset_corrigido/classes.txt
   
   Funcionalidade:
   - Detecta produtos
   - Permite correção manual das detecções
   - Exporta dataset corrigido para retreinamento

# ============================================================
# 🎯 FLUXO DE TRABALHO RECOMENDADO
# ============================================================

1. Captura de Imagens
   └─> Upload via interface web ou API
       └─> Salvo em: media/produtos_treino/{produto_id}/

2. Treinamento Inicial
   └─> Execute: python treinar_modelo_yolo.py
       └─> Cria: verifik/dataset_yolo/
       └─> Gera: verifik/verifik_yolov8.pt

3. Adicionar Novos Produtos (Incremental)
   └─> Execute: python treinar_incremental.py
       └─> Usa checkpoint: verifik/verifik_yolov8.pt
       └─> Atualiza modelo sem perder aprendizado anterior

4. Teste de Detecção
   └─> Execute: python testar_deteccao.py caminho/foto.jpg
       └─> Resultados em: resultados_deteccao/teste/

5. Correção de Erros
   └─> Execute: python detector_simples.py
       └─> Corrija detecções manualmente
       └─> Dataset corrigido em: dataset_corrigido/
       └─> Retreine com dados corrigidos

# ============================================================
# 📝 OBSERVAÇÕES IMPORTANTES
# ============================================================

1. **Datasets Temporários**:
   - verifik/dataset_treino/{timestamp}/ são TEMPORÁRIOS
   - Criados a cada treinamento
   - Podem ser deletados após treino bem-sucedido
   - Ocupam espaço em disco

2. **Checkpoint vs Modelo Final**:
   - Checkpoint (last.pt): Último estado do treino (pode não ser o melhor)
   - Best Model (best.pt): Melhor modelo durante treino (validação)
   - Modelo Final (verifik_yolov8.pt): Cópia do melhor para produção

3. **Prioridade de Busca de Modelo**:
   Ordem de busca automática:
   1. verifik/verifik_yolov8.pt (produção)
   2. verifik/runs/treino_verifik/weights/best.pt (melhor)
   3. verifik/runs/treino_verifik/weights/last.pt (último)

4. **Banco de Dados vs Arquivos**:
   - Banco: Metadados (produto, ordem, timestamps)
   - Arquivos: Imagens físicas (media/)
   - Ambos precisam estar sincronizados

# ============================================================
# 🚀 PRÓXIMOS PASSOS SUGERIDOS
# ============================================================

1. ✅ Verificar imagens não treinadas:
   - 398 imagens no banco
   - Verificar quais já foram usadas em treino
   - Campo: ImagemProduto.usada_treino (se existir)

2. ✅ Limpar datasets temporários:
   - Remover verifik/dataset_treino/* (exceto mais recente)
   - Liberar espaço em disco

3. ✅ Organizar imagens:
   - 166 produtos sem imagens precisam de fotos
   - Priorizar produtos mais vendidos

4. ✅ Backup do modelo:
   - Fazer cópia de verifik/verifik_yolov8.pt
   - Antes de qualquer retreinamento

5. ✅ Documentar classes:
   - Criar lista de classes treinadas
   - Manter sincronizado com banco de dados
"""

print(__doc__)
