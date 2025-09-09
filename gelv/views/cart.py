from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_POST
from gelv.utils import get_request_content, trace
from gelv.models import Issue, Subscription, Payment
from gelv.cart import Cart, CartItem

PAYMENT_METHODS = [
    {'id': 'bank_transfer', 'name': 'bank transfer', 'description': 'manual bank transfer'},
]

BILLING_DETAILS_FIELDS = [
    {'id': 'billing_email', 'name': 'email', 'type': 'email', 'autocomplete': 'email'},
    {'id': 'name', 'name': 'name', 'type': 'text', 'autocomplete': 'name'},
    {'id': 'phone', 'name': 'phone number', 'type': 'tel', 'autocomplete': 'tel'},
    {'id': 'personal_code', 'name': 'personal code', 'type': 'text', 'autocomplete': ''},
    {'id': 'city', 'name': 'city', 'type': 'text', 'autocomplete': 'address-level2'},
    {'id': 'address', 'name': 'street address', 'type': 'text', 'autocomplete': 'address-line1'},
    {'id': 'postal_code', 'name': 'postal code', 'type': 'text', 'autocomplete': 'postal-code'},
]


@login_required
def cart_view(request: HttpRequest) -> HttpResponse:
    """Display cart items from session and payment method selection"""
    # get cart from session
    cart = Cart.from_session(request.session)

    context = {
        'user': request.user,
        'latest_payment': Payment.get_latest(request.user),
        'cart_subscriptions': cart.filter_by_type(Subscription),
        'cart_issues': cart.filter_by_type(Issue),
        'total': cart.total_price,
        'payment_methods': PAYMENT_METHODS,
        'billing_fields': BILLING_DETAILS_FIELDS,
    }

    trace(cart, 'cart')
    return render(request, 'cart/cart.html', context)


def clear_cart(request: HttpRequest) -> HttpResponse:
    """Clear all items from cart"""
    request.session['cart'] = []
    request.session.modified = True
    messages.success(request, 'Cart cleared')
    return redirect(request.META.get('HTTP_REFERER', 'catalogue'))


@require_POST
def add_to_cart(request: HttpRequest) -> HttpResponse:
    """Add item to cart"""
    cart = Cart.from_session(request.session)
    item = CartItem.from_singleton_request(request)
    success = cart.add(item)

    if success:
        request.session['cart'] = cart.raw
        request.session.modified = True
        messages.success(request, f'{item.product} added to cart')
    else:
        messages.info(request, f'{item.product} is already in cart')

    trace(f"cart is now {cart}")
    return redirect(request.META.get('HTTP_REFERER', 'catalogue'))


@require_POST
def remove_from_cart(request: HttpRequest) -> HttpResponse:
    """Remove item from cart"""
    cart = Cart.from_session(request.session)
    item = CartItem.from_singleton_request(request)
    success = cart.remove(item)

    if success:
        request.session['cart'] = cart.raw
        request.session.modified = True
        messages.success(request, f'{item.product} removed from cart')

    else:
        messages.info(request, f'{item.product} is not in cart')

    trace(f"cart is now {cart}")
    return redirect(request.META.get('HTTP_REFERER', 'catalogue'))


@require_POST
def change_subscription_start(request: HttpRequest) -> HttpResponse:
    """Change metadata['start'] of a subscription"""
    cart = Cart.from_session(request.session)
    item = CartItem.from_singleton_request(request)
    success = cart.edit_meta(item, start=int(get_request_content(request).get('new_start', 0)))

    if success:
        request.session['cart'] = cart.raw
        request.session.modified = True
    else:
        messages.info(request, 'Something went wrong.')

    trace(f"cart is now {cart}")

    return redirect(request.META.get('HTTP_REFERER', 'catalogue'))
