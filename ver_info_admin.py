"""
Mostra informações do usuário admin
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from accounts.models import User

# Buscar usuário admin
admin_user = User.objects.filter(username='admin').first()

if admin_user:
    print("╔════════════════════════════════════════════════════════════╗")
    print("║              INFORMAÇÕES DO USUÁRIO ADMIN                  ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    print(f"👤 Username: {admin_user.username}")
    print(f"📧 Email: {admin_user.email}")
    print(f"👨 Nome: {admin_user.get_full_name() or '(não definido)'}")
    print(f"🔑 Superusuário: {'Sim' if admin_user.is_superuser else 'Não'}")
    print(f"✅ Ativo: {'Sim' if admin_user.is_active else 'Não'}")
    print(f"📅 Data de criação: {admin_user.date_joined}")
    print()
    print("🔐 PARA FAZER LOGIN USE:")
    print(f"   Email: {admin_user.email}")
    print("   Senha: M@rcio1309")
    print()
    print("🌐 URLs:")
    print("   Admin: http://127.0.0.1:8000/admin/")
    print("   Login: http://127.0.0.1:8000/login/")
else:
    print("❌ Usuário admin não encontrado!")
