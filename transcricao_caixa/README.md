# 📸 Sistema de Transcrição de Caixa

Sistema para transcrição automática de imagens de documentos fiscais (notas, cupons, recibos) para fechamento de caixa de empresas.

## 🎯 Objetivo

Automatizar o processo de fechamento de caixa através de:
- Upload de fotos de documentos fiscais
- Transcrição automática via OCR
- Revisão e correção manual
- Cálculo automático de totais
- Fechamento completo por empresa/data

## 📦 Funcionalidades

### ✅ Implementado

- **Modelos de Dados:**
  - `Empresa` - Cadastro de empresas
  - `TipoDocumento` - Tipos de documentos (NF, Cupom, Recibo, etc.)
  - `FechamentoCaixa` - Fechamento por empresa/data
  - `DocumentoTranscrito` - Documentos individuais transcritos
  - `ItemDocumento` - Itens de cada documento

- **Admin Django:**
  - Gestão completa de empresas
  - Gestão de tipos de documentos
  - Visualização e edição de fechamentos
  - Processamento de documentos
  - Actions para processar em lote

- **Views e URLs:**
  - Dashboard inicial com estatísticas
  - Lista e criação de fechamentos
  - Upload de documentos
  - Revisão de documentos transcritos
  - APIs para processamento em lote

### 🚧 A Implementar

- **OCR Integration:**
  - [ ] Tesseract OCR (local)
  - [ ] Google Vision API (cloud)
  - [ ] AWS Textract (cloud)
  - [ ] Azure Computer Vision (cloud)

- **Processamento Inteligente:**
  - [ ] Detecção automática de tipo de documento
  - [ ] Extração de campos específicos (número, data, valor)
  - [ ] Detecção de itens em notas fiscais
  - [ ] Validação de valores calculados

- **Templates HTML:**
  - [ ] index.html - Dashboard
  - [ ] lista_fechamentos.html
  - [ ] novo_fechamento.html
  - [ ] detalhe_fechamento.html
  - [ ] upload_documento.html
  - [ ] revisar_documento.html

- **Melhorias:**
  - [ ] Upload múltiplo de imagens
  - [ ] Pré-processamento de imagens (rotação, contraste)
  - [ ] Exportação para Excel/PDF
  - [ ] Relatórios gerenciais
  - [ ] Integração com sistema contábil

## 🗄️ Estrutura de Dados

### Empresa
- Nome, CNPJ, Endereço
- Status ativo/inativo
- Auditoria (criado em, atualizado em)

### FechamentoCaixa
- Empresa, Data do fechamento
- Status (rascunho → processamento → revisão → concluído)
- Totais calculados (vendas, despesas, líquido)
- Contadores de documentos

### DocumentoTranscrito
- Fechamento, Tipo de documento
- Imagem original e processada
- Texto completo (OCR)
- Dados estruturados (número, data, valor)
- Confiança do OCR
- Status e revisão

### ItemDocumento
- Descrição, quantidade, valores
- Código, unidade
- Ordenação

## 🚀 Como Usar

### 1. Criar Empresa
```python
python manage.py shell
from transcricao_caixa.models import Empresa
empresa = Empresa.objects.create(nome="Posto ABC", cnpj="12.345.678/0001-90")
```

### 2. Criar Fechamento
Via admin ou interface web, criar fechamento para uma data específica

### 3. Upload de Documentos
Fazer upload das fotos de notas/cupons via interface

### 4. Processar OCR
Sistema extrai texto automaticamente (quando OCR implementado)

### 5. Revisar e Corrigir
Revisar dados extraídos e fazer correções necessárias

### 6. Concluir Fechamento
Marcar como concluído para gerar relatório final

## 🔧 Próximos Passos

1. **Implementar OCR** - Integrar Tesseract ou API de OCR
2. **Criar Templates** - Interfaces HTML para usuários
3. **Testar com dados reais** - Validar extração com documentos reais
4. **Otimizar performance** - Processamento em background (Celery)
5. **Adicionar relatórios** - Exportação e visualizações

## 📊 Tecnologias

- **Django** - Framework web
- **Pillow** - Processamento de imagens
- **OCR** (a implementar) - Tesseract/Google Vision/AWS Textract
- **Bootstrap** - Interface responsiva
- **jQuery** - Interatividade

## 🔗 Integração com projeto principal

Este sistema está no branch `feature/sistema-transcricao-caixa` e poderá ser integrado ao projeto principal após testes.

---

**Status:** 🟡 Em Desenvolvimento  
**Branch:** `feature/sistema-transcricao-caixa`  
**Última atualização:** 26/11/2025
