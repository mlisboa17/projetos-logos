from rest_framework import serializers
from .models import (
    Funcionario, PerfilGestor, Produto, OperacaoVenda, ItemVenda,
    DeteccaoProduto, Incidente, EvidenciaIncidente, Alerta,
    Camera, CameraStatus
)
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class FuncionarioSerializer(serializers.ModelSerializer):
    usuario_info = UserSerializer(source='usuario', read_only=True)
    
    class Meta:
        model = Funcionario
        fields = '__all__'


class PerfilGestorSerializer(serializers.ModelSerializer):
    usuario_info = UserSerializer(source='usuario', read_only=True)
    
    class Meta:
        model = PerfilGestor
        fields = '__all__'


class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = '__all__'


class ItemVendaSerializer(serializers.ModelSerializer):
    produto_info = ProdutoSerializer(source='produto', read_only=True)
    
    class Meta:
        model = ItemVenda
        fields = '__all__'


class OperacaoVendaSerializer(serializers.ModelSerializer):
    funcionario_info = FuncionarioSerializer(source='funcionario', read_only=True)
    itens = ItemVendaSerializer(many=True, read_only=True)
    
    class Meta:
        model = OperacaoVenda
        fields = '__all__'


class DeteccaoProdutoSerializer(serializers.ModelSerializer):
    camera_info = serializers.StringRelatedField(source='camera', read_only=True)
    produto_info = ProdutoSerializer(source='produto_identificado', read_only=True)
    
    class Meta:
        model = DeteccaoProduto
        fields = '__all__'


class EvidenciaIncidenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenciaIncidente
        fields = '__all__'


class IncidenteSerializer(serializers.ModelSerializer):
    funcionario_info = FuncionarioSerializer(source='funcionario', read_only=True)
    camera_info = serializers.StringRelatedField(source='camera', read_only=True)
    operacao_venda_info = serializers.StringRelatedField(source='operacao_venda', read_only=True)
    deteccao_info = DeteccaoProdutoSerializer(source='deteccao', read_only=True)
    evidencias = EvidenciaIncidenteSerializer(many=True, read_only=True)
    
    class Meta:
        model = Incidente
        fields = '__all__'


class AlertaSerializer(serializers.ModelSerializer):
    destinatario_info = UserSerializer(source='destinatario', read_only=True)
    incidente_info = serializers.StringRelatedField(source='incidente', read_only=True)
    camera_info = serializers.StringRelatedField(source='camera', read_only=True)
    
    class Meta:
        model = Alerta
        fields = '__all__'


class CameraStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraStatus
        fields = '__all__'


class CameraSerializer(serializers.ModelSerializer):
    ultimo_status = serializers.SerializerMethodField()
    total_deteccoes = serializers.SerializerMethodField()
    total_incidentes = serializers.SerializerMethodField()
    
    class Meta:
        model = Camera
        fields = '__all__'
        extra_kwargs = {
            'senha': {'write_only': True}  # Não expor senha na API
        }
    
    def get_ultimo_status(self, obj):
        ultimo = obj.historico_status.order_by('-data_hora').first()
        if ultimo:
            return CameraStatusSerializer(ultimo).data
        return None
    
    def get_total_deteccoes(self, obj):
        return obj.deteccaoproduto_set.count()
    
    def get_total_incidentes(self, obj):
        return obj.incidente_set.count()
