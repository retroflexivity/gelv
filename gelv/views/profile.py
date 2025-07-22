from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from ..models import Product


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    """User profile view with purchased products"""
    
    # get user's purchased products
    purchased_products = Product.objects.filter(
        order__user=request.user,
        order__status=True
    ).distinct()
    
    context = {
        'user': request.user,
        'purchased_products': purchased_products,
    }
    return render(request, 'registration/profile.html', context)
