from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from gelv.models import Post


def home_view(request: HttpRequest) -> HttpResponse:
    """Home page with news"""

    context = {
        'posts': Post.objects.all(),
    }

    return render(request, 'home/home.html', context)
