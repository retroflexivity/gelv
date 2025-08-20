from django import template

register = template.Library()

@register.filter
def item(lst, i):
    return lst.get(i, None)
