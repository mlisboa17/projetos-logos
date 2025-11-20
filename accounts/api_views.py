from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import Organization, User
from .serializers import (
    OrganizationSerializer, 
    UserSerializer, 
    UserCreateSerializer,
    UserLoginSerializer
)


class OrganizationViewSet(viewsets.ModelViewSet):
    """ViewSet para Organizations - apenas usuários autenticados"""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtra organizations baseado no usuário"""
        user = self.request.user
        
        # Super admin vê todas
        if user.is_super_admin or user.is_superuser:
            return Organization.objects.all()
        
        # Usuários veem apenas sua organização
        return Organization.objects.filter(id=user.organization_id)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet para Users"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtra users baseado no usuário logado"""
        user = self.request.user
        
        # Super admin vê todos
        if user.is_super_admin or user.is_superuser:
            return User.objects.all()
        
        # Org admin vê usuários da sua organização
        if user.is_org_admin:
            return User.objects.filter(organization=user.organization)
        
        # Usuário comum vê apenas ele mesmo
        return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Retorna dados do usuário logado"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def pending(self, request):
        """Lista usuários pendentes de aprovação (apenas super admins)"""
        if not (request.user.is_super_admin or request.user.is_superuser):
            return Response(
                {"detail": "Sem permissão para visualizar usuários pendentes."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pending_users = User.objects.filter(is_active=False)
        serializer = self.get_serializer(pending_users, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """Aprova um usuário pendente (apenas super admins)"""
        if not (request.user.is_super_admin or request.user.is_superuser):
            return Response(
                {"detail": "Sem permissão para aprovar usuários."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        user.is_active = True
        user.save()
        
        serializer = self.get_serializer(user)
        return Response({
            "message": f"Usuário {user.username} aprovado com sucesso!",
            "user": serializer.data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        """Rejeita e deleta um usuário pendente (apenas super admins)"""
        if not (request.user.is_super_admin or request.user.is_superuser):
            return Response(
                {"detail": "Sem permissão para rejeitar usuários."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        username = user.username
        user.delete()
        
        return Response({
            "message": f"Usuário {username} rejeitado e removido."
        })


class AuthViewSet(viewsets.ViewSet):
    """ViewSet para autenticação"""
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """Registra novo usuário (aguarda aprovação)"""
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Cadastro realizado com sucesso! Aguarde aprovação do administrador.",
                "user": UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Login de usuário e geração de tokens JWT"""
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            user = authenticate(username=username, password=password)
            
            if user is None:
                return Response(
                    {"detail": "Credenciais inválidas."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            if not user.is_active:
                return Response(
                    {"detail": "Conta aguardando aprovação do administrador."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Gerar tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "message": "Login realizado com sucesso!",
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout do usuário"""
        return Response({
            "message": "Logout realizado com sucesso!"
        })
