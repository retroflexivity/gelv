from django.http import HttpRequest, HttpResponse, QueryDict
from django.utils import timezone
from django.shortcuts import redirect
from datetime import date
import json
import logging
from num2words import num2words  # type: ignore
from typing import TypeAlias, Any

JSON: TypeAlias = dict[str, Any]

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


def trace(x, comment='trace'):
    logger.debug(comment + ': ' + str(x))
    return x


class IssueNumber:
    number: int
    year: int

    anno_number = 1
    anno_year = 2010

    def __init__(self, n, frequency=12):
        self.year = self.anno_year + n // 12
        self.number = self.anno_number + n % 12

    def __str__(self):
        return f'{self.number}/{self.year}'


def get_request_content(request: HttpRequest) -> JSON | QueryDict:
    if request.content_type == 'application/json':
        return json.loads(request.body)
    else:
        return request.POST


IssueN = int


def diff_month(d1: date, d2: date) -> int:
    return (d1.year - d2.year) * 12 + d1.month - d2.month


def add_month(d: date, months: int) -> date:
    return date((d.year + months // 12), (d.month + months % 12), 1)


def current_month_year() -> date:
    return timezone.now().replace(day=1)


def smart_redirect(request: HttpRequest, default: str = 'home') -> HttpResponse:
    return redirect(request.META.get('HTTP_REFERER', default))


def verbalize_price(price, language='lv') -> str:
    euros = num2words(round(price), lang=language)
    if language == 'lv':
        return f'{euros} eiro 00 centi'.capitalize()
    else:
        raise NotImplementedError
