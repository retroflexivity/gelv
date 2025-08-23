from django.contrib import messages
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.http import require_POST
from ..utils import get_request_content, trace
from ..models import Issue, Subscription

PAYMENT_METHODS = [
    {'id': 'klix', 'name': 'Klix', 'description': 'Card, online bank, Google Pay, Apple Pay'},
    {'id': 'bank_transfer', 'name': 'Bank transfer', 'description': 'Manual bank transfer'},
]


def get_cart_count(request: HttpRequest) -> HttpResponse:
    """Get total number of items in cart"""
    cart = request.session.get('cart', [])
    return JsonResponse({'cart_count': len(cart)})


def get_item_from_request(request: HttpRequest) -> tuple[str, int]:
    """Get item kind and id from a cart modification request"""
    data = get_request_content(request)

    kind = data.get('product_kind', 'none')
    id = int(data.get('product_id', 0))
    return kind, id


def get_issue_and_sub_ids(cart: list) -> tuple[list[int], list[int]]:
    issue_ids = [id for kind, id in cart if kind == 'issue']
    sub_ids = [id for kind, id in cart if kind == 'subscription']
    return issue_ids, sub_ids


def get_issues_and_subs(cart: list) -> tuple[QuerySet[Issue], QuerySet[Subscription]]:
    """Get issues and subscriptions from cart as two lists."""
    issue_ids, sub_ids = get_issue_and_sub_ids(cart)
    return Issue.get_objects(ids=issue_ids), Subscription.get_objects(ids=sub_ids)


def cart_view(request: HttpRequest) -> HttpResponse:
    """Display cart items from session and payment method selection"""
    # get cart from session
    cart = request.session.get('cart', [])
    issues, subs = get_issues_and_subs(cart)

    total = sum(issue.price for issue in issues) + sum(sub.price for sub in subs)

    context = {
        'user': request.user,
        'cart_issues': list(issues),
        'cart_subscriptions': list(subs),
        'total': total,
        'payment_methods': PAYMENT_METHODS
    }

    return render(request, 'cart/cart.html', context)


def verify_and_get_item_name(kind: str, id: int) -> str:
    """Verify an item exists and get its name"""
    if kind == 'issue':
        return str(get_object_or_404(Issue, id=id))
    elif kind == 'subscription':
        return str(get_object_or_404(Subscription, id=id))
    else:
        raise TypeError(f'Unsupported product kind {kind}')


def clear_cart(request: HttpRequest) -> HttpResponse:
    """Clear all items from cart"""
    request.session['cart'] = []
    request.session.modified = True
    messages.success(request, 'Cart cleared')
    return redirect(request.META.get('HTTP_REFERER', 'catalogue'))


@require_POST
def add_to_cart(request: HttpRequest) -> HttpResponse:
    """Add item to cart"""
    kind, id = get_item_from_request(request)
    name = verify_and_get_item_name(kind, id)

    # add if not already in cart
    cart = request.session.get('cart', [])
    if [kind, id] not in cart:
        print(f"adding {kind} {id} to cart")
        cart.append((kind, id))
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, f'{name} added to cart')
    else:
        messages.info(request, f'{name} is already in cart')

    return redirect(request.META.get('HTTP_REFERER', 'catalogue'))


@require_POST
def remove_from_cart(request: HttpRequest) -> HttpResponse:
    """Remove item from cart"""
    kind, id = get_item_from_request(request)
    name = verify_and_get_item_name(kind, id)

    # remove if in cart
    cart = request.session.get('cart', [])
    if [kind, id] in cart:
        cart.remove([kind, id])
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, f'{name} removed from cart')

    else:
        messages.info(request, f'{name} is not in cart')

    return redirect(request.META.get('HTTP_REFERER', 'catalogue'))
