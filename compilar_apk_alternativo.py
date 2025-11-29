
# APK COMPILATION - ALTERNATIVE APPROACH
# Installing minimal dependencies and using simplified buildozer config

import subprocess
import sys
import os

def install_minimal_deps():
    '''Install only essential packages'''
    deps = [
        'buildozer==1.5.0',
        'kivy==2.3.0',  
        'pillow',
        'cython==0.29.36'
    ]
    
    for dep in deps:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
            print(f"✅ Installed: {dep}")
        except:
            print(f"❌ Failed: {dep}")

def create_minimal_buildozer_spec():
    '''Create minimal buildozer.spec with fewer dependencies'''
    
    spec_content = '''[app]
title = VerifiK Mobile
package.name = verifik_coleta
package.domain = com.logos.verifik

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,db

version = 1.0
requirements = python3,kivy==2.3.0,pillow
icon.filename = icon.png

[buildozer]
log_level = 1
warn_on_root = 0

[app:android]
archs = armeabi-v7a
api = 33
minapi = 21
ndk = 25b
accept_sdk_license = True
'''

    with open('buildozer_minimal.spec', 'w') as f:
        f.write(spec_content)
    
    print("✅ Created minimal buildozer.spec")

def build_apk_minimal():
    '''Build APK with minimal configuration'''
    
    print("🔄 Building APK with minimal setup...")
    
    # Set environment variables
    os.environ['BUILDOZER_WARN_ON_ROOT'] = '0'
    os.environ['ANDROID_HOME'] = '/opt/android-sdk'
    
    try:
        # Clean previous builds
        subprocess.run(['buildozer', 'android', 'clean'], check=False)
        
        # Build debug APK
        result = subprocess.run([
            'buildozer', '-v', 'android', 'debug',
            '--buildozer-spec', 'buildozer_minimal.spec'
        ], capture_output=True, text=True, timeout=1800)
        
        if result.returncode == 0:
            print("✅ APK BUILD SUCCESS!")
            return True
        else:
            print(f"❌ Build failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def create_web_version():
    '''Create a web-based version as fallback'''
    
    html_content = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VerifiK Mobile - Web Version</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        
        .container {
            max-width: 400px;
            margin: 0 auto;
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .logo {
            width: 80px;
            height: 80px;
            background: white;
            border-radius: 15px;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            color: #667eea;
            font-weight: bold;
        }
        
        .camera-area {
            width: 100%;
            height: 200px;
            background: rgba(0,0,0,0.3);
            border: 2px dashed rgba(255,255,255,0.5);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 20px 0;
            cursor: pointer;
        }
        
        .buttons {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        
        .btn {
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn:active {
            transform: scale(0.95);
        }
        
        .btn-primary {
            background: #4CAF50;
            color: white;
        }
        
        .btn-secondary {
            background: #2196F3;
            color: white;
        }
        
        .product-list {
            margin-top: 20px;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .product-item {
            background: rgba(255,255,255,0.1);
            padding: 10px;
            margin: 5px 0;
            border-radius: 8px;
            cursor: pointer;
        }
        
        .status {
            text-align: center;
            margin: 20px 0;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">VK</div>
            <h1>VerifiK Mobile</h1>
            <p>Sistema de Coleta de Imagens</p>
        </div>
        
        <div class="camera-area" onclick="captureImage()">
            <p>📸 Toque para capturar imagem</p>
        </div>
        
        <select id="productSelect" style="width: 100%; padding: 10px; border-radius: 8px; margin: 10px 0;">
            <option value="">Selecionar produto...</option>
        </select>
        
        <div class="buttons">
            <button class="btn btn-primary" onclick="saveImage()">💾 Salvar</button>
            <button class="btn btn-secondary" onclick="exportData()">📤 Exportar</button>
        </div>
        
        <div class="status" id="status">
            Pronto para uso
        </div>
        
        <div class="product-list" id="productList">
            <!-- Produtos serão listados aqui -->
        </div>
    </div>

    <script>
        // Dados dos produtos (simulado)
        const products = [
            'Produto A - Categoria 1',
            'Produto B - Categoria 2', 
            'Produto C - Categoria 3',
            'Produto D - Categoria 1',
            'Produto E - Categoria 2'
        ];
        
        let capturedImages = [];
        
        function loadProducts() {
            const select = document.getElementById('productSelect');
            products.forEach(product => {
                const option = document.createElement('option');
                option.value = product;
                option.textContent = product;
                select.appendChild(option);
            });
        }
        
        function captureImage() {
            // Simular captura de imagem
            const status = document.getElementById('status');
            status.textContent = '📸 Imagem capturada!';
            
            // Aqui seria integrado com a câmera real do dispositivo
            // navigator.camera ou getUserMedia()
            
            setTimeout(() => {
                status.textContent = 'Selecione um produto para associar a imagem';
            }, 1500);
        }
        
        function saveImage() {
            const product = document.getElementById('productSelect').value;
            const status = document.getElementById('status');
            
            if (!product) {
                status.textContent = '⚠️ Selecione um produto primeiro';
                return;
            }
            
            capturedImages.push({
                product: product,
                timestamp: new Date().toLocaleString(),
                image: 'captured_image_' + Date.now()
            });
            
            status.textContent = `✅ Imagem salva para: ${product}`;
            updateProductList();
        }
        
        function exportData() {
            const status = document.getElementById('status');
            
            if (capturedImages.length === 0) {
                status.textContent = '⚠️ Nenhuma imagem para exportar';
                return;
            }
            
            // Criar CSV com os dados
            let csv = 'Produto,Data/Hora,Arquivo\n';
            capturedImages.forEach(item => {
                csv += `"${item.product}","${item.timestamp}","${item.image}"\n`;
            });
            
            // Download do arquivo
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'verifik_coleta_' + new Date().toISOString().split('T')[0] + '.csv';
            a.click();
            
            status.textContent = '📤 Dados exportados com sucesso!';
        }
        
        function updateProductList() {
            const list = document.getElementById('productList');
            list.innerHTML = '<h3>Imagens Capturadas:</h3>';
            
            capturedImages.forEach((item, index) => {
                const div = document.createElement('div');
                div.className = 'product-item';
                div.innerHTML = `
                    <strong>${item.product}</strong><br>
                    <small>${item.timestamp}</small>
                `;
                list.appendChild(div);
            });
        }
        
        // Inicializar
        window.onload = function() {
            loadProducts();
        }
    </script>
</body>
</html>'''
    
    with open('verifik_mobile_web.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Created web version: verifik_mobile_web.html")

def main():
    print("🚀 VERIFIK MOBILE - COMPILATION ALTERNATIVE")
    print("=" * 50)
    
    # Try minimal APK build first
    install_minimal_deps()
    create_minimal_buildozer_spec()
    
    success = build_apk_minimal()
    
    if not success:
        print("\n🌐 Creating web version as fallback...")
        create_web_version()
        print("\n📱 You can use the web version on mobile browsers")
        print("   Open verifik_mobile_web.html in any mobile browser")
    
    print("\n✅ PROCESS COMPLETED!")

if __name__ == "__main__":
    main()
