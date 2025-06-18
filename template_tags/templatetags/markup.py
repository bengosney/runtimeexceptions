from django import template

register = template.Library()


@register.filter
def nbsp(value):
    return value.replace(" ", "\xa0") if isinstance(value, str) else value
