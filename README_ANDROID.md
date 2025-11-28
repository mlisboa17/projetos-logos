# 📱 VerifiK Mobile - Sistema de Coleta para Android

Sistema móvel de coleta de imagens para funcionários, otimizado para dispositivos Android com interface touch-friendly.

## 🎯 Principais Funcionalidades

### 📸 Captura de Imagens
- **Câmera nativa**: Tire fotos diretamente no app
- **Galeria**: Selecione imagens já existentes
- **Preview em tempo real**: Visualize antes de anotar

### ✏️ Anotações Interativas
- **Touch & drag**: Marque produtos tocando e arrastando
- **Multiple annotations**: Vários produtos na mesma imagem
- **Visualização em tempo real**: Veja as marcações enquanto desenha

### 💾 Armazenamento Local
- **SQLite integrado**: Dados salvos localmente no dispositivo
- **Trabalha offline**: Não precisa de internet para coletar
- **Sincronização**: Exporta dados quando conectado

### 🔄 Sincronização
- **Exportação JSON**: Dados em formato padronizado
- **Upload automático**: Envia para servidor quando disponível
- **Backup seguro**: Dados protegidos localmente

## 🛠️ Como Compilar

### Pré-requisitos
- Python 3.8+
- Kivy 2.3.0+
- Buildozer
- Android SDK (instalado automaticamente)

### Compilação Rápida

#### Windows:
```bash
# Executar script automático
build_android.bat
```

#### Linux/Mac:
```bash
# Dar permissão e executar
chmod +x build_android.sh
./build_android.sh
```

#### Manual:
```bash
# Instalar dependências
pip install buildozer cython

# Compilar APK debug
buildozer android debug

# Compilar APK release (assinado)
buildozer android release
```

## 📱 Instalação no Dispositivo

1. **Habilitar fontes desconhecidas**:
   - Configurações → Segurança → Fontes desconhecidas ✅

2. **Transferir APK**:
   - Via USB, email, ou cloud storage
   - Arquivo gerado em: `bin/VerifiK_Mobile_Coleta-3.0.0-debug.apk`

3. **Instalar**:
   - Toque no arquivo APK
   - Seguir instruções na tela

## 🎮 Como Usar o App

### 1️⃣ Seleção de Produto
```
🎯 1. Selecione o Produto
├── Spinner com lista de produtos
├── 🔄 Botão "Atualizar Lista"
└── ✅ Produto selecionado fica destacado
```

### 2️⃣ Captura de Imagem
```
📷 2. Capture ou Carregue Imagem
├── 📷 Câmera (foto nova)
├── 🖼️ Galeria (imagem existente)
└── 👁️ Preview da imagem
```

### 3️⃣ Anotação
```
✏️ 3. Marque o Produto na Imagem
├── Toque e arraste na imagem
├── 🧽 Limpar marcações
└── Múltiplas marcações por imagem
```

### 4️⃣ Salvamento
```
💾 4. Salvar e Exportar
├── 📝 Campo observações (opcional)
├── 💾 Salvar Anotação (banco local)
└── 📤 Exportar Dados (arquivo JSON)
```

## 🗃️ Estrutura de Dados

### Banco SQLite Local
```sql
-- Tabela de produtos
CREATE TABLE produtos (
    id INTEGER PRIMARY KEY,
    descricao_produto TEXT NOT NULL,
    marca TEXT,
    ativo INTEGER DEFAULT 1,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de imagens coletadas
CREATE TABLE imagens_coletadas (
    id INTEGER PRIMARY KEY,
    produto_id INTEGER,
    caminho_imagem TEXT,
    anotacoes TEXT, -- JSON das coordenadas
    observacoes TEXT,
    data_coleta DATETIME DEFAULT CURRENT_TIMESTAMP,
    sincronizado INTEGER DEFAULT 0,
    FOREIGN KEY (produto_id) REFERENCES produtos (id)
);
```

### Formato de Exportação (JSON)
```json
{
  "timestamp": "2025-11-28T10:30:00",
  "total_imagens": 5,
  "imagens": [
    {
      "id": 1,
      "produto_id": 2,
      "produto_nome": "Coca-Cola 350ml",
      "produto_marca": "Coca-Cola",
      "caminho_imagem": "/storage/emulated/0/DCIM/IMG_001.jpg",
      "anotacoes": [
        {
          "start": [120, 200],
          "end": [280, 350],
          "color": [1, 0, 0, 1]
        }
      ],
      "observacoes": "Produto bem visível na prateleira",
      "data_coleta": "2025-11-28T10:25:00"
    }
  ]
}
```

## 🔧 Configurações Técnicas

### Permissões Android
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<uses-permission android:name="android.permission.WAKE_LOCK" />
```

### Requisitos do Sistema
- **Android**: 5.0+ (API 21+)
- **Arquitetura**: ARM64, ARMv7
- **RAM**: 2GB mínimo, 4GB recomendado
- **Armazenamento**: 100MB + espaço para fotos
- **Câmera**: Obrigatória para captura

## 📊 Recursos de Performance

### ⚡ Otimizações Mobile
- Interface responsiva para diferentes tamanhos de tela
- Scroll suave em listas longas
- Compressão automática de imagens
- Cache inteligente de produtos

### 💾 Gerenciamento de Memória
- Carregamento sob demanda de imagens
- Limpeza automática de cache
- Compactação de banco SQLite
- Gerenciamento de thumbnails

### 🔋 Economia de Bateria
- Modo sleep automático
- Otimização de CPU
- Compressão de dados
- Sync apenas com Wi-Fi (opcional)

## 🐛 Troubleshooting

### Problemas Comuns

#### ❌ Erro de compilação
```bash
# Limpar cache e tentar novamente
buildozer android clean
buildozer android debug
```

#### 📱 App não instala
- Verificar se "Fontes desconhecidas" está habilitado
- Desinstalar versão anterior primeiro
- Verificar espaço disponível no dispositivo

#### 📷 Câmera não funciona
- Verificar permissões do app nas configurações
- Reiniciar o aplicativo
- Verificar se outra app está usando a câmera

#### 💾 Dados não salvam
- Verificar permissões de armazenamento
- Verificar espaço disponível
- Verificar se o produto foi selecionado

## 📈 Roadmap

### Versão 3.1 (Próxima)
- [ ] Sincronização automática com servidor
- [ ] Modo offline melhorado
- [ ] Compressão de imagens
- [ ] Upload em background

### Versão 3.2 (Futuro)
- [ ] Reconhecimento automático de produtos (IA)
- [ ] Interface em múltiplos idiomas
- [ ] Relatórios de produtividade
- [ ] Integração com APIs externas

## 📞 Suporte

Para dúvidas ou problemas:
1. Verificar este README primeiro
2. Consultar logs do buildozer
3. Testar em dispositivo diferente
4. Entrar em contato com a equipe de desenvolvimento

---

**🎉 VerifiK Mobile v3.0.0 - Coleta Inteligente de Imagens**  
*Desenvolvido para máxima produtividade em campo* 📱✨