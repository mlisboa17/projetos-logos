"""
Reset senha do admin
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from accounts.models import User

# Buscar admin
admin = User.objects.filter(username='admin').first()

if admin:
    # Resetar senha
    admin.set_password('M@rcio1309')
    admin.save()
    
    print("✅ Senha resetada com sucesso!")
    print()
    print("=" * 60)
    print("CREDENCIAIS DE LOGIN:")
    print("=" * 60)
    print(f"Email: {admin.email}")
    print("Senha: M@rcio1309")
    print("=" * 60)
    print()
    print("Tente fazer login em: http://127.0.0.1:8000/login/")
else:
    print("❌ Usuário admin não encontrado!")
