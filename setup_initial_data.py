"""
Script para criar Organization e Superuser inicial
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from accounts.models import Organization, User

# Criar Grupo Lisboa
org, created = Organization.objects.get_or_create(
    slug='grupo-lisboa',
    defaults={
        'name': 'Grupo Lisboa',
        'type': 'holding',
        'email': 'contato@grupolisboa.com.br',
        'phone': '(81) 3333-3333',
        'city': 'Recife',
        'state': 'PE',
        'subscription_plan': 'enterprise',
        'subscription_status': 'active',
        'max_stores': 999,
        'max_users': 999,
        'max_cameras': 999,
        'max_erp_integrations': 999,
        'monthly_price': 0,
    }
)

if created:
    print(f"✅ Organização criada: {org.name}")
else:
    print(f"✅ Organização já existe: {org.name}")

# Criar superuser
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='marcio@grupolisboa.com.br',
        password='M@rcio1309',
        organization=org,
        first_name='Márcio',
        last_name='Lisboa',
        is_org_admin=True,
        is_super_admin=True
    )
    print(f"✅ Superusuário criado: {admin.username}")
    print(f"   Email: marcio@grupolisboa.com.br")
    print(f"   Senha: M@rcio1309")
else:
    admin = User.objects.get(username='admin')
    admin.email = 'marcio@grupolisboa.com.br'
    admin.set_password('M@rcio1309')
    admin.first_name = 'Márcio'
    admin.last_name = 'Lisboa'
    admin.save()
    print(f"✅ Superusuário atualizado: {admin.username}")
    print(f"   Email: marcio@grupolisboa.com.br")
    print(f"   Senha: M@rcio1309")

print("\n🎉 Setup completo!")
print("\n🚀 Execute: python manage.py runserver")
print("📱 Acesse: http://localhost:8000/admin")
