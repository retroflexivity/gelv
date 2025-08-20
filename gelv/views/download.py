from django.shortcuts import render
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.contrib.auth.decorators import login_required
from ..models import User


@login_required
def download_view(request: HttpRequest, id) -> HttpResponse:
    user = User.get_by_email(request.user.email)
    owned_issue_ids = user.get_owned_issues().values_list('id', flat=True)

    if id in owned_issue_ids:
        return HttpResponse(f'here is issue {id}')
    else:
        return HttpResponse(f'you do not own issue {id}')
