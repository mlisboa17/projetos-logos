"""
Cria ou atualiza o usuário admin
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Tentar encontrar usuário admin existente
admin_user = User.objects.filter(username='admin').first()

if admin_user:
    print("✓ Usuário 'admin' já existe")
    print(f"  Email: {admin_user.email}")
    print(f"  Superusuário: {admin_user.is_superuser}")
    print(f"  Ativo: {admin_user.is_active}")
    
    # Atualizar senha
    admin_user.set_password('M@rcio1309')
    admin_user.is_superuser = True
    admin_user.is_staff = True
    admin_user.is_active = True
    admin_user.save()
    print("\n✅ Senha atualizada para: M@rcio1309")
else:
    # Criar novo usuário
    admin_user = User.objects.create_superuser(
        username='admin',
        email='admin@verifik.com',
        password='M@rcio1309'
    )
    print("✅ Usuário 'admin' criado com sucesso!")
    print(f"   Email: {admin_user.email}")
    print(f"   Senha: M@rcio1309")

print("\n🔑 Credenciais de acesso:")
print("   Usuário: admin")
print("   Senha: M@rcio1309")
print("   URL: http://127.0.0.1:8000/admin/")
