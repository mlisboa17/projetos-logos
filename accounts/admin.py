"""
Django Admin para Accounts
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Organization, User


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'subscription_plan', 'subscription_status', 'is_active', 'created_at']
    list_filter = ['type', 'subscription_plan', 'subscription_status', 'is_active']
    search_fields = ['name', 'email', 'cnpj']
    readonly_fields = ['created_at', 'updated_at', 'subscription_started_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'slug', 'type', 'cnpj')
        }),
        ('Contato', {
            'fields': ('email', 'phone', 'address', 'city', 'state')
        }),
        ('Assinatura', {
            'fields': (
                'subscription_plan', 'subscription_status',
                'subscription_started_at', 'subscription_expires_at',
                'max_stores', 'max_users', 'max_cameras', 'max_erp_integrations'
            )
        }),
        ('White-Label', {
            'fields': ('logo', 'primary_color', 'secondary_color', 'custom_domain'),
            'classes': ('collapse',)
        }),
        ('Billing', {
            'fields': ('monthly_price',)
        }),
        ('Metadata', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'get_full_name', 'organization', 'is_org_admin', 'is_active']
    list_filter = ['is_active', 'is_staff', 'is_org_admin', 'is_super_admin', 'organization']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar')}),
        ('Organização', {'fields': ('organization', 'is_org_admin', 'is_super_admin')}),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Datas Importantes', {
            'fields': ('last_login', 'last_login_at', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'organization'),
        }),
    )

