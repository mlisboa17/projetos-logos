from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import User, Organization, UserOrganization
from .forms import UserRegistrationForm


def home(request):
    """Homepage view - Landing page do LOGOS"""
    context = {
        'user_authenticated': request.user.is_authenticated,
    }
    
    if request.user.is_authenticated:
        # Usuário logado - mostrar funcionalidades
        context['active_organization'] = request.user.active_organization
        context['organizations'] = request.user.organizations_access.all()
        
        # Verificar permissões
        if request.user.active_organization:
            try:
                user_org = UserOrganization.objects.get(
                    user=request.user,
                    organization=request.user.active_organization
                )
                context['permissions'] = {
                    'can_access_verifik': user_org.can_access_verifik,
                    'can_access_erp_hub': user_org.can_access_erp_hub,
                    'can_access_fuel_prices': user_org.can_access_fuel_prices,
                    'is_org_admin': user_org.is_org_admin,
                }
            except UserOrganization.DoesNotExist:
                context['permissions'] = {}
    
    return render(request, 'home.html', context)


def api_test(request):
    """API Testing Interface"""
    return render(request, 'api_test.html')


@login_required
def switch_organization(request, org_id):
    """Troca a organização ativa do usuário"""
    try:
        # Verificar se o usuário tem acesso a essa organização
        user_org = UserOrganization.objects.get(
            user=request.user,
            organization_id=org_id
        )
        
        # Atualizar organização ativa
        request.user.active_organization = user_org.organization
        request.user.save()
        
        messages.success(request, f'Organização alterada para: {user_org.organization.name}')
        
    except UserOrganization.DoesNotExist:
        messages.error(request, 'Você não tem acesso a essa organização.')
    
    # Redirecionar de volta para a página anterior
    return redirect(request.META.get('HTTP_REFERER', '/'))


def register(request):
    """User registration view - requires super user approval"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Create user but keep inactive until approved
            user = form.save(commit=False)
            user.is_active = False  # User starts inactive
            user.save()
            
            # Notify super users about new registration
            notify_superusers_new_registration(user)
            
            messages.success(
                request, 
                'Cadastro realizado com sucesso! '
                'Sua conta será ativada após aprovação do administrador. '
                'Você receberá um e-mail quando sua conta for aprovada.'
            )
            return redirect('registration_pending')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def registration_pending(request):
    """Show pending registration message"""
    return render(request, 'accounts/registration_pending.html')


@login_required
@user_passes_test(lambda u: u.is_super_admin or u.is_superuser)
def pending_users(request):
    """List all pending user registrations (only super admins)"""
    pending = User.objects.filter(is_active=False).order_by('-date_joined')
    return render(request, 'accounts/pending_users.html', {'pending_users': pending})


@login_required
@user_passes_test(lambda u: u.is_super_admin or u.is_superuser)
def approve_user(request, user_id):
    """Approve a pending user registration"""
    user = User.objects.get(id=user_id)
    user.is_active = True
    user.save()
    
    # Send approval email
    send_approval_email(user)
    
    messages.success(request, f'Usuário {user.username} aprovado com sucesso!')
    return redirect('pending_users')


@login_required
@user_passes_test(lambda u: u.is_super_admin or u.is_superuser)
def reject_user(request, user_id):
    """Reject and delete a pending user registration"""
    user = User.objects.get(id=user_id)
    username = user.username
    user.delete()
    
    messages.warning(request, f'Usuário {username} rejeitado e removido.')
    return redirect('pending_users')


def notify_superusers_new_registration(user):
    """Notify all super users about new registration"""
    superusers = User.objects.filter(is_super_admin=True, is_active=True)
    
    for admin in superusers:
        try:
            send_mail(
                subject='LOGOS - Nova Solicitação de Cadastro',
                message=f'''
Olá {admin.first_name},

Um novo usuário solicitou cadastro na plataforma LOGOS:

Nome: {user.first_name} {user.last_name}
E-mail: {user.email}
Organização: {user.organization.name}
Data: {user.date_joined.strftime('%d/%m/%Y %H:%M')}

Acesse o painel administrativo para aprovar ou rejeitar esta solicitação:
http://localhost:8000/admin/pending-users/

Atenciosamente,
Sistema LOGOS
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Erro ao enviar email para {admin.email}: {e}")


def send_approval_email(user):
    """Send approval email to user"""
    try:
        send_mail(
            subject='LOGOS - Cadastro Aprovado! 🎉',
            message=f'''
Olá {user.first_name},

Sua conta na plataforma LOGOS foi aprovada!

Você já pode acessar o sistema com suas credenciais:
E-mail: {user.email}

Acesse: http://localhost:8000/admin

Bem-vindo(a) ao LOGOS!

Atenciosamente,
Equipe Grupo Lisboa
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Erro ao enviar email de aprovação: {e}")


def user_login(request):
    """View de login"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Seu cadastro ainda não foi aprovado.')
        else:
            messages.error(request, 'Email ou senha incorretos.')
    
    return render(request, 'accounts/login.html')


def user_logout(request):
    """View de logout"""
    logout(request)
    messages.success(request, 'Você saiu com sucesso.')
    return redirect('home')
