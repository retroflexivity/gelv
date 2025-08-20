from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction
import json

from ..utils import get_request_content
from .cart import get_issues_and_subs, PAYMENT_METHODS
from ..models import IssueOrder, SubscriptionOrder, User, Payment


@require_POST
@transaction.atomic
def process_payment(request: HttpRequest) -> HttpResponse:
    """Process payment and create orders"""
    print("init payment")
    data = get_request_content(request)
    payment_method = data.get('payment_method')
    email = data.get('email')

    cart = request.session.get('cart', [])
    if not cart:
        messages.error(request, 'Cart is empty')
        return redirect(request.META.get('HTTP_REFERER', 'catalogue'))
    cart_issues, cart_subs = get_issues_and_subs(cart)

    # validate payment method
    valid_methods = [method['id'] for method in PAYMENT_METHODS]
    if payment_method not in valid_methods:
        messages.error(request, 'Invalid payment method')
        return redirect(request.META.get('HTTP_REFERER', 'cart'))

    # get user
    if not email:
        messages.error(request, 'Email is required')
        return redirect(request.META.get('HTTP_REFERER', 'cart'))
    user = User.get_by_email(email)
    if not user:
        # # create new user
        # user = User(
        #     first_name=user_info.get('first_name', ''),
        #     last_name=user_info.get('last_name', ''),
        #     email=email,
        #     phone=user_info.get('phone', ''),
        #     password=''  # Handle password separately during registration
        # )
        # user.register()
        messages.error(request, 'Email is required')
        return redirect(request.META.get('HTTP_REFERER', 'cart'))

    # check if user already owns any of the issues
    existing_orders = IssueOrder.objects.filter(
        payment__user=user,
        product__in=cart_issues,
    )

    if existing_orders.exists():
        owned_issues = [order.product for order in existing_orders]
        messages.error(request, f'You already own {", ".join(map(str, owned_issues))}')
        return redirect(request.META.get('HTTP_REFERER', 'cart'))

    # process payment
    # TODO: make it real
    payment_success = True

    if not payment_success:
        messages.error(request, 'Payment failed')
        return redirect(request.META.get('HTTP_REFERER', 'cart'))

    # create a single Payment and Orders for each product
    payment = Payment.new(user=user)
    for sub in cart_subs:
        SubscriptionOrder.new(sub, payment=payment).id
    for issue in cart_issues:
        IssueOrder.new(issue, payment=payment).id

    # clear cart from session
    request.session['cart'] = []
    request.session.modified = True

    # TODO: send receipts

    messages.success(request, 'Purchase completed successfully!')
    return redirect('catalogue')


# Webhook for payment confirmations (if needed)
@csrf_exempt
@require_POST
def payment_webhook(request: HttpRequest) -> HttpResponse:
    """Handle payment webhooks from payment providers"""
    data = json.loads(request.body)

    # TODO: Implement webhook signature verification
    if data.get('type') == 'payment_intent.succeeded':
        # Update order status based on payment reference
        payment_reference = data.get('payment_reference')
        # You'd need to add a payment_reference field to your Order model
        # or use another way to match payments to orders

    return JsonResponse({'status': 'success'})
