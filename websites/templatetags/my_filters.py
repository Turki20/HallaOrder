from django import template

register = template.Library()

@register.filter
def dict_items(value):
    if isinstance(value, dict):
        return value.items()
    return []
