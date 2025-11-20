from rest_framework import serializers
from .models import Organization, User


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer para Organization"""
    
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'type', 'cnpj', 'email', 'phone',
            'address', 'city', 'state', 'subscription_plan', 
            'subscription_status', 'subscription_started_at', 
            'subscription_expires_at', 'max_stores', 'max_users',
            'max_cameras', 'max_erp_integrations', 'logo',
            'primary_color', 'secondary_color', 'custom_domain',
            'monthly_price', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer para User"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'avatar', 'organization', 'organization_name',
            'is_org_admin', 'is_super_admin', 'is_active',
            'last_login_at', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de usuário"""
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'phone', 'organization'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.is_active = False  # Requer aprovação
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer para login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
