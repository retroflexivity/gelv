from django import template
from gelv.utils import IssueNumber, trace

register = template.Library()


@register.filter
def item(a, key):
    return a.get(key, None)


@register.filter
def attr(a, key):
    return getattr(a, key, None)


@register.filter
def format_issue_number(n):
    return str(IssueNumber(n))


@register.filter
def len_range(start, length):
    return range(start, int(start) + int(length))
