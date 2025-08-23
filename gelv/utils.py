from django.http import HttpRequest, QueryDict
from django.utils import timezone
from datetime import date
import json
import logging
from typing import TypeAlias

JSON: TypeAlias = dict[str, str]

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


def trace(x, comment='trace'):
    logger.debug(comment + ': ' + str(x))
    return x


def get_request_content(request: HttpRequest) -> JSON | QueryDict:
    if request.content_type == 'application/json':
        return json.loads(request.body)
    else:
        return request.POST


def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month


def add_month(d, months):
    return date((d.year + months // 12), (d.month + months % 12), 1)


def current_month_year():
    return timezone.now().replace(day=1)
