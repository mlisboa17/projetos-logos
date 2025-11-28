"""
Servidor HTTP simples para servir o banco de dados SQLite
Execute este script para disponibilizar o banco via HTTP
"""
import http.server
import socketserver
import os
from pathlib import Path

# Configurações
PORTA = 8080
ARQUIVO_BANCO = "db.sqlite3"

class BancoDadosHandler(http.server.SimpleHTTPRequestHandler):
    """Handler customizado que sempre serve o arquivo db.sqlite3"""
    
    def do_GET(self):
        """Serve o banco de dados para qualquer requisição"""
        if self.path == '/' or self.path == '/db.sqlite3' or self.path == '/banco':
            # Caminho do banco
            banco_path = Path(__file__).parent / ARQUIVO_BANCO
            
            if not banco_path.exists():
                self.send_error(404, f"Banco de dados não encontrado: {banco_path}")
                return
            
            # Enviar arquivo
            self.send_response(200)
            self.send_header("Content-type", "application/x-sqlite3")
            self.send_header("Content-Disposition", f"attachment; filename={ARQUIVO_BANCO}")
            self.send_header("Content-Length", str(banco_path.stat().st_size))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            with open(banco_path, 'rb') as f:
                self.wfile.write(f.read())
            
            print(f"✅ Banco enviado para {self.client_address[0]}")
        else:
            self.send_error(404, "Use /db.sqlite3 ou /banco para baixar o banco de dados")
    
    def log_message(self, format, *args):
        """Log customizado"""
        print(f"[{self.log_date_time_string()}] {format % args}")

def obter_ip_local():
    """Obtém o IP local da máquina"""
    import socket
    try:
        # Criar socket temporário para descobrir IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    # Verificar se banco existe
    banco_path = Path(__file__).parent / ARQUIVO_BANCO
    if not banco_path.exists():
        print(f"❌ ERRO: Banco de dados não encontrado!")
        print(f"   Esperado em: {banco_path}")
        return
    
    tamanho_mb = banco_path.stat().st_size / (1024 * 1024)
    
    print("="*70)
    print("🌐 SERVIDOR HTTP - BANCO DE DADOS SQLITE")
    print("="*70)
    print(f"\n📁 Arquivo: {ARQUIVO_BANCO}")
    print(f"📊 Tamanho: {tamanho_mb:.2f} MB")
    print(f"🔌 Porta: {PORTA}")
    
    ip_local = obter_ip_local()
    
    print(f"\n📡 URLs para download:")
    print(f"   Local:  http://localhost:{PORTA}/banco")
    print(f"   Rede:   http://{ip_local}:{PORTA}/banco")
    
    print(f"\n💡 Use estas URLs no sistema standalone:")
    print(f"   LINK_ONEDRIVE_BANCO = \"http://{ip_local}:{PORTA}/banco\"")
    
    print(f"\n⚠️  IMPORTANTE:")
    print(f"   - Este servidor deve ficar rodando enquanto outros sistemas")
    print(f"     precisarem baixar o banco de dados")
    print(f"   - Certifique-se que a porta {PORTA} não está bloqueada no firewall")
    print(f"   - Computadores na mesma rede podem acessar via http://{ip_local}:{PORTA}/banco")
    
    print(f"\n🛑 Para parar o servidor: Pressione Ctrl+C")
    print("="*70)
    print()
    
    # Iniciar servidor
    with socketserver.TCPServer(("", PORTA), BancoDadosHandler) as httpd:
        try:
            print(f"✅ Servidor iniciado com sucesso!")
            print(f"🔄 Aguardando requisições...\n")
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Servidor encerrado pelo usuário")
            print("="*70)

if __name__ == "__main__":
    main()
