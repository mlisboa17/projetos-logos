#!/usr/bin/env python
"""
Script para visualizar imagens processadas em uma galeria web
"""
import django
import os
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser
import json
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from acessorios.models import ProcessadorImagens


class ImagemHandler(SimpleHTTPRequestHandler):
    """Handler customizado para servir imagens processadas"""
    
    def do_GET(self):
        if self.path == '/':
            self.enviar_html_galeria()
        elif self.path == '/api/imagens':
            self.enviar_json_imagens()
        else:
            super().do_GET()
    
    def enviar_html_galeria(self):
        """Envia HTML da galeria"""
        html = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Galeria de Imagens Processadas</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .stat-card h3 {
            color: #667eea;
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .stat-card p {
            color: #666;
            font-size: 0.9em;
        }
        
        .filtros {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .filtros label {
            font-weight: bold;
            color: #333;
        }
        
        .filtros select,
        .filtros input {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 0.9em;
        }
        
        .filtros button {
            padding: 8px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        }
        
        .filtros button:hover {
            background: #764ba2;
        }
        
        .galeria {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .imagem-card {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
            cursor: pointer;
        }
        
        .imagem-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.2);
        }
        
        .imagem-container {
            width: 100%;
            height: 250px;
            overflow: hidden;
            background: #f0f0f0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .imagem-container img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
        
        .imagem-info {
            padding: 15px;
        }
        
        .imagem-info h3 {
            color: #333;
            font-size: 0.9em;
            margin-bottom: 5px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .imagem-info p {
            color: #666;
            font-size: 0.8em;
            margin-bottom: 3px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 0.75em;
            font-weight: bold;
            margin-top: 5px;
        }
        
        .status-sucesso {
            background: #d4edda;
            color: #155724;
        }
        
        .status-erro {
            background: #f8d7da;
            color: #721c24;
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.8);
        }
        
        .modal-content {
            background-color: white;
            margin: auto;
            padding: 20px;
            border-radius: 10px;
            width: 90%;
            max-width: 800px;
            max-height: 90vh;
            overflow: auto;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }
        
        .modal-close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .modal-close:hover {
            color: black;
        }
        
        .modal-img {
            width: 100%;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px;
            color: white;
        }
        
        .empty-state h2 {
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖼️ Galeria de Imagens Processadas</h1>
        
        <div class="stats">
            <div class="stat-card">
                <h3 id="total-processadas">0</h3>
                <p>Imagens Processadas</p>
            </div>
            <div class="stat-card">
                <h3 id="total-sucesso">0</h3>
                <p>Com Sucesso</p>
            </div>
            <div class="stat-card">
                <h3 id="total-erros">0</h3>
                <p>Com Erros</p>
            </div>
        </div>
        
        <div class="filtros">
            <label for="filtro-tipo">Tipo:</label>
            <select id="filtro-tipo">
                <option value="">Todos</option>
                <option value="remover_fundo">Remover Fundo</option>
                <option value="redimensionar">Redimensionar</option>
                <option value="normalizar">Normalizar Cores</option>
                <option value="aumentar_contraste">Aumentar Contraste</option>
            </select>
            
            <label for="filtro-status">Status:</label>
            <select id="filtro-status">
                <option value="">Todos</option>
                <option value="sucesso">Sucesso</option>
                <option value="erro">Erro</option>
            </select>
            
            <label for="filtro-busca">Busca:</label>
            <input type="text" id="filtro-busca" placeholder="Nome da imagem...">
            
            <button onclick="aplicarFiltros()">Filtrar</button>
        </div>
        
        <div class="galeria" id="galeria">
            <div class="empty-state">
                <h2>Carregando imagens...</h2>
            </div>
        </div>
    </div>
    
    <div id="modal" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="fecharModal()">&times;</span>
            <img id="modal-img" class="modal-img" src="" alt="">
            <div id="modal-info"></div>
        </div>
    </div>
    
    <script>
        let todasAsImagens = [];
        
        function carregarImagens() {
            fetch('/api/imagens')
                .then(r => r.json())
                .then(data => {
                    todasAsImagens = data;
                    atualizarStats(data);
                    renderizarGaleria(data);
                })
                .catch(e => console.error('Erro:', e));
        }
        
        function atualizarStats(imagens) {
            const total = imagens.length;
            const sucesso = imagens.filter(i => i.status === 'sucesso').length;
            const erros = imagens.filter(i => i.status === 'erro').length;
            
            document.getElementById('total-processadas').textContent = total;
            document.getElementById('total-sucesso').textContent = sucesso;
            document.getElementById('total-erros').textContent = erros;
        }
        
        function renderizarGaleria(imagens) {
            const galeria = document.getElementById('galeria');
            
            if (imagens.length === 0) {
                galeria.innerHTML = '<div class="empty-state"><h2>Nenhuma imagem encontrada</h2></div>';
                return;
            }
            
            galeria.innerHTML = imagens.map(img => `
                <div class="imagem-card" onclick="abrirModal('${img.imagem_processada}', '${img.tipo}', '${img.status}', '${img.data_criacao}')">
                    <div class="imagem-container">
                        ${img.status === 'sucesso' ? 
                            `<img src="/${img.imagem_processada}" alt="Imagem processada" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22300%22 height=%22250%22%3E%3Crect fill=%22%23f0f0f0%22 width=%22300%22 height=%22250%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 font-family=%22Arial%22 font-size=%2214%22 fill=%22%23999%22%3EImagem não encontrada%3C/text%3E%3C/svg%3E'">` 
                            : `<div style="text-align: center; color: #999;"><p>Erro</p><p style="font-size: 0.8em;">Clique para ver detalhes</p></div>`
                        }
                    </div>
                    <div class="imagem-info">
                        <h3 title="${img.imagem_processada}">${img.imagem_processada.split('/').pop()}</h3>
                        <p>Tipo: ${img.tipo}</p>
                        <p>${img.data_criacao}</p>
                        <span class="status-badge status-${img.status}">
                            ${img.status === 'sucesso' ? '✓ Sucesso' : '✗ Erro'}
                        </span>
                    </div>
                </div>
            `).join('');
        }
        
        function aplicarFiltros() {
            const tipo = document.getElementById('filtro-tipo').value;
            const status = document.getElementById('filtro-status').value;
            const busca = document.getElementById('filtro-busca').value.toLowerCase();
            
            let filtradas = todasAsImagens;
            
            if (tipo) filtradas = filtradas.filter(i => i.tipo === tipo);
            if (status) filtradas = filtradas.filter(i => i.status === status);
            if (busca) filtradas = filtradas.filter(i => 
                i.imagem_processada.toLowerCase().includes(busca) ||
                i.imagem_original.toLowerCase().includes(busca)
            );
            
            renderizarGaleria(filtradas);
        }
        
        function abrirModal(imagem, tipo, status, data) {
            const modal = document.getElementById('modal');
            const img = document.getElementById('modal-img');
            const info = document.getElementById('modal-info');
            
            img.src = '/' + imagem;
            info.innerHTML = `
                <h3>${imagem.split('/').pop()}</h3>
                <p><strong>Tipo:</strong> ${tipo}</p>
                <p><strong>Status:</strong> ${status}</p>
                <p><strong>Data:</strong> ${data}</p>
            `;
            
            modal.style.display = 'block';
        }
        
        function fecharModal() {
            document.getElementById('modal').style.display = 'none';
        }
        
        window.onclick = function(event) {
            const modal = document.getElementById('modal');
            if (event.target === modal) modal.style.display = 'none';
        }
        
        // Carregar imagens ao iniciar
        carregarImagens();
        
        // Atualizar a cada 5 segundos
        setInterval(carregarImagens, 5000);
    </script>
</body>
</html>
        '''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def enviar_json_imagens(self):
        """Envia JSON com dados das imagens processadas"""
        imagens = []
        
        for proc in ProcessadorImagens.objects.all().order_by('-data_criacao'):
            imagens.append({
                'id': proc.id,
                'tipo': proc.get_tipo_display(),
                'imagem_original': proc.imagem_original,
                'imagem_processada': proc.imagem_processada,
                'status': proc.status,
                'data_criacao': proc.data_criacao.strftime('%d/%m/%Y %H:%M:%S'),
                'mensagem_erro': proc.mensagem_erro or '',
            })
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(imagens).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suprime logs de acesso"""
        pass


class GaleriaImagens:
    """Servidor de galeria de imagens"""
    
    def __init__(self, porta=8001):
        self.porta = porta
        self.servidor = None
    
    def iniciar(self):
        """Inicia o servidor e abre o navegador"""
        os.chdir('.')
        
        self.servidor = HTTPServer(('127.0.0.1', self.porta), ImagemHandler)
        
        url = f'http://127.0.0.1:{self.porta}'
        
        print(f"\n{'='*80}")
        print(f"🖼️  GALERIA DE IMAGENS PROCESSADAS")
        print(f"{'='*80}")
        print(f"\n✅ Servidor rodando em: {url}")
        print(f"📱 Abrindo navegador...")
        print(f"\nPressione CTRL+C para parar\n")
        
        # Abrir navegador
        try:
            webbrowser.open(url)
        except:
            print(f"⚠️  Abra manualmente: {url}")
        
        try:
            self.servidor.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✅ Servidor parado")


if __name__ == '__main__':
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    galeria = GaleriaImagens(porta)
    galeria.iniciar()
