# CONFIGURAÇÃO DO SISTEMA DE DETECÇÃO ORGANIZADO
# ================================================

# Caminhos dos modelos (ordem de prioridade)
MODELOS_YOLO = [
    "verifik/verifik_yolov8.pt",        # Modelo treinado específico
    "verifik/runs/treino_continuado/weights/best.pt",  # Modelo de treinamento
    "yolov8s.pt",                       # Modelo médio
    "yolov8n.pt"                        # Modelo leve
]

# Configurações de detecção
DETECCAO_CONFIG = {
    'confianca_minima': 0.25,
    'iou_threshold': 0.45,
    'max_deteccoes': 20,
    'area_minima_percentual': 1.0  # Mínimo 1% da imagem
}

# Configurações de OCR
OCR_CONFIG = {
    'tesseract_path': r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    'idiomas': 'eng+por',
    'configs': [
        '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        '--psm 6',
        '--psm 7'
    ]
}

# Regiões do rótulo para análise (percentuais)
REGIOES_ROTULO = [
    # (nome, x1%, y1%, x2%, y2%)
    ("centro_superior", 0.2, 0.1, 0.8, 0.5),      # Centro-superior
    ("centro_meio", 0.15, 0.3, 0.85, 0.7),        # Centro-meio
    ("superior_largo", 0.1, 0.05, 0.9, 0.4),      # Superior completo
    ("meio_largo", 0.1, 0.25, 0.9, 0.75),         # Meio completo
    ("foco_marca", 0.25, 0.15, 0.75, 0.45)        # Foco na marca
]

# Base de conhecimento de marcas
MARCAS_CONHECIDAS = {
    'HEINEKEN': {
        'padroes': ['HEINEKEN', 'HEINE', 'NEKEN', 'HEINEK', 'HEINKEN'],
        'padroes_parciais': ['HEIN', 'NEKEN', 'EINEK'],
        'cores_tipicas': [(34, 139, 34), (0, 100, 0)],  # Verde
        'categoria': 'CERVEJA',
        'volumes_comuns': ['350ML', '473ML', '600ML', '330ML']
    },
    'DEVASSA': {
        'padroes': ['DEVASSA', 'DEVAS', 'EVASSA', 'VASSA', 'DEVASA'],
        'padroes_parciais': ['DEVA', 'EVAS', 'VASS'],
        'cores_tipicas': [(255, 0, 0), (139, 0, 0)],    # Vermelho
        'categoria': 'CERVEJA',
        'volumes_comuns': ['350ML', '473ML', '600ML']
    },
    'BUDWEISER': {
        'padroes': ['BUDWEISER', 'BUDWEI', 'BUD', 'WEISER', 'BUDWISER'],
        'padroes_parciais': ['BUDW', 'WEIS', 'BWEI'],
        'cores_tipicas': [(255, 255, 255), (220, 220, 220)],  # Branco/Prata
        'categoria': 'CERVEJA',
        'volumes_comuns': ['330ML', '350ML', '473ML']
    },
    'AMSTEL': {
        'padroes': ['AMSTEL', 'AMSTE', 'MATEL', 'AMSTEI'],
        'padroes_parciais': ['AMST', 'STEL', 'MSTE'],
        'cores_tipicas': [(255, 215, 0), (255, 140, 0)],  # Dourado
        'categoria': 'CERVEJA',
        'volumes_comuns': ['350ML', '473ML']
    },
    'STELLA': {
        'padroes': ['STELLA', 'ARTOIS', 'STELA', 'STELLA ARTOIS'],
        'padroes_parciais': ['STEL', 'TELA', 'ARTOI'],
        'cores_tipicas': [(255, 215, 0), (255, 140, 0)],  # Dourado
        'categoria': 'CERVEJA',
        'volumes_comuns': ['330ML', '473ML']
    },
    'BRAHMA': {
        'padroes': ['BRAHMA', 'BRAMA', 'RAHMA', 'BRAHM'],
        'padroes_parciais': ['BRAH', 'RAHM', 'AHMA'],
        'cores_tipicas': [(255, 255, 255), (255, 0, 0)],  # Branco/Vermelho
        'categoria': 'CERVEJA',
        'volumes_comuns': ['350ML', '473ML', '600ML']
    },
    'SKOL': {
        'padroes': ['SKOL', 'SK0L', 'KOLL', '5KOL'],
        'padroes_parciais': ['SKO', 'KOL'],
        'cores_tipicas': [(0, 0, 255), (255, 255, 255)],  # Azul/Branco
        'categoria': 'CERVEJA',
        'volumes_comuns': ['350ML', '473ML']
    },
    'ANTARCTICA': {
        'padroes': ['ANTARCTICA', 'ANTARTIC', 'ANTART', 'ANTARTICA'],
        'padroes_parciais': ['ANTAR', 'ARTIC', 'CTICA'],
        'cores_tipicas': [(0, 0, 255), (255, 255, 255)],  # Azul/Branco
        'categoria': 'CERVEJA',
        'volumes_comuns': ['350ML', '473ML']
    },
    'PEPSI': {
        'padroes': ['PEPSI', 'P3PSI', 'PEPS', 'PEPSY'],
        'padroes_parciais': ['PEPS', 'EPSI'],
        'cores_tipicas': [(0, 0, 255), (255, 0, 0)],      # Azul/Vermelho
        'categoria': 'REFRIGERANTE',
        'volumes_comuns': ['350ML', '473ML', '600ML', '1L', '2L']
    },
    'COCA': {
        'padroes': ['COCA', 'COLA', 'COCACOLA', 'COCA COLA'],
        'padroes_parciais': ['COC', 'OCA', 'COL'],
        'cores_tipicas': [(255, 0, 0), (139, 0, 0)],      # Vermelho
        'categoria': 'REFRIGERANTE',
        'volumes_comuns': ['350ML', '473ML', '600ML', '1L', '2L']
    },
    'KAISER': {
        'padroes': ['KAISER', 'KAISE', 'ISER', 'KAYSER'],
        'padroes_parciais': ['KAIS', 'AISE', 'ISER'],
        'cores_tipicas': [(255, 215, 0), (139, 69, 19)],  # Dourado/Marrom
        'categoria': 'CERVEJA',
        'volumes_comuns': ['350ML', '473ML']
    },
    'ITAIPAVA': {
        'padroes': ['ITAIPAVA', 'ITAIP', 'PAVA', 'ITAIPAV'],
        'padroes_parciais': ['ITAI', 'PAVA', 'TAIP'],
        'cores_tipicas': [(255, 215, 0), (255, 255, 255)],  # Dourado/Branco
        'categoria': 'CERVEJA',
        'volumes_comuns': ['350ML', '473ML']
    }
}

# Volumes comuns para validação
VOLUMES_CONHECIDOS = [
    '269ML', '330ML', '350ML', '355ML', '473ML', '500ML', '600ML',
    '1L', '1.5L', '2L', '2.5L'
]

# Configurações de debug
DEBUG_CONFIG = {
    'salvar_regioes_rotulo': True,
    'salvar_preprocessamento': True,
    'salvar_produtos_individuais': True,
    'verbose_ocr': True
}