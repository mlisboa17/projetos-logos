from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import User, Organization
from .forms import UserRegistrationForm


def home(request):
    """Homepage view"""
    return render(request, 'home.html')


def api_test(request):
    """API Testing Interface"""
    return render(request, 'api_test.html')


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
