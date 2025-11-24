from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Permite acessar item de dicionário no template"""
    if dictionary is None:
        return None
    return dictionary.get(key)
