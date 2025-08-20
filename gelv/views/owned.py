from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from ..models import User


@login_required
def owned_view(request: HttpRequest) -> HttpResponse:
    """User profile view with purchased products"""

    # get user's purchased products
    user = User.get_by_email(request.user.email)
    owned_issues = user.get_owned_issues()

    context = {
        'user': user,
        'products': owned_issues,
    }
    return render(request, 'account/owned.html', context)
