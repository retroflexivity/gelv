from django import template
from random import sample
from gelv.models import Ad

register = template.Library()


@register.simple_tag
def random_ads(k) -> list[Ad]:
    return sample(list(Ad.get_active()), k=k)
