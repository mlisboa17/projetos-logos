from django import forms
from .models import ProdutoMae, CodigoBarrasProdutoMae, ImagemProduto


class ProdutoMaeForm(forms.ModelForm):
    class Meta:
        model = ProdutoMae
        fields = ['descricao_produto', 'marca', 'tipo', 'preco', 'imagem_referencia', 'ativo']
        widgets = {
            'descricao_produto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: CERVEJA HEINEKEN LATA 350ML'
            }),
            'marca': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Heineken'
            }),
            'tipo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: CERVEJA'
            }),
            'preco': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'imagem_referencia': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class CodigoBarrasForm(forms.ModelForm):
    class Meta:
        model = CodigoBarrasProdutoMae
        fields = ['codigo', 'principal']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '7896045505340'
            }),
            'principal': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class ImagemProdutoForm(forms.ModelForm):
    class Meta:
        model = ImagemProduto
        fields = ['imagem', 'descricao', 'ordem', 'ativa']
        widgets = {
            'imagem': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'descricao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descrição da imagem'
            }),
            'ordem': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 0
            }),
            'ativa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


# Formsets para múltiplos códigos e imagens
from django.forms import inlineformset_factory

CodigoBarrasFormSet = inlineformset_factory(
    ProdutoMae,
    CodigoBarrasProdutoMae,
    form=CodigoBarrasForm,
    extra=3,
    can_delete=True
)

ImagemProdutoFormSet = inlineformset_factory(
    ProdutoMae,
    ImagemProduto,
    form=ImagemProdutoForm,
    extra=5,
    can_delete=True
)
