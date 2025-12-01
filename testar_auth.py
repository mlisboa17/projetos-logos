"""
Teste completo de autenticação
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logos.settings')
django.setup()

from django.contrib.auth import authenticate
from accounts.models import User

print("=" * 60)
print("TESTE DE AUTENTICAÇÃO")
print("=" * 60)

# Buscar usuário
email = "marcio@grupolisboa.com.br"
user = User.objects.filter(email=email).first()

if user:
    print(f"\n✓ Usuário encontrado: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  Ativo: {user.is_active}")
    print(f"  Superusuário: {user.is_superuser}")
    print(f"  Staff: {user.is_staff}")
    print(f"  Organização ativa: {user.active_organization}")
    
    # Testar autenticação
    print("\n" + "=" * 60)
    print("TESTANDO AUTENTICAÇÃO")
    print("=" * 60)
    
    # Teste 1: Com email
    auth1 = authenticate(username=email, password='M@rcio1309')
    print(f"\n1. authenticate(username='{email}', password='M@rcio1309')")
    print(f"   Resultado: {auth1}")
    
    # Teste 2: Com username
    auth2 = authenticate(username=user.username, password='M@rcio1309')
    print(f"\n2. authenticate(username='{user.username}', password='M@rcio1309')")
    print(f"   Resultado: {auth2}")
    
    # Verificar senha
    print("\n" + "=" * 60)
    print("VERIFICAÇÃO DE SENHA")
    print("=" * 60)
    check = user.check_password('M@rcio1309')
    print(f"\nSenha 'M@rcio1309' está correta? {check}")
    
    if not check:
        print("\n⚠️ SENHA INCORRETA! Resetando...")
        user.set_password('M@rcio1309')
        user.save()
        print("✓ Senha resetada")
        
        # Testar novamente
        auth3 = authenticate(username=email, password='M@rcio1309')
        print(f"\n3. Após reset - authenticate(username='{email}')")
        print(f"   Resultado: {auth3}")
    
    print("\n" + "=" * 60)
    print("BACKENDS DE AUTENTICAÇÃO")
    print("=" * 60)
    from django.conf import settings
    backends = getattr(settings, 'AUTHENTICATION_BACKENDS', ['django.contrib.auth.backends.ModelBackend'])
    for backend in backends:
        print(f"  - {backend}")
    
else:
    print(f"\n❌ Usuário com email {email} NÃO ENCONTRADO!")
    
    # Listar todos os usuários
    print("\nUsuários cadastrados:")
    for u in User.objects.all():
        print(f"  - {u.username} ({u.email})")
