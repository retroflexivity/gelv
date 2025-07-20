from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction
import json

from ..models import Product, User, Order


@login_required
def cart_view(request: HttpRequest) -> HttpResponse:
    """Display cart items from session and payment method selection"""
    # get cart from session
    cart = request.session.get('cart', [])
    
    if cart:
        # get list of products
        products = Product.get_by_ids(cart)
        cart_items = list(products)
        total = sum(product.price for product in products)
    else:
        cart_items = []
        total = 0
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'payment_methods': [
            {'id': 'stripe', 'name': 'Credit Card (Stripe)', 'description': 'Pay with credit/debit card'},
            {'id': 'paypal', 'name': 'PayPal', 'description': 'Pay with PayPal account'},
            {'id': 'bank_transfer', 'name': 'Bank Transfer', 'description': 'Manual bank transfer'},
        ]
    }
    
    return render(request, 'cart/cart.html', context)


@require_POST # type: ignore
def add_to_cart(request: HttpRequest) -> HttpResponse:
    """Add item to cart"""
    try:
        data = json.loads(request.body)
        product_id = int(data.get('product_id'))
        
        # verify product exists
        product = get_object_or_404(Product, id=int(product_id))
        
        # get cart from session or create empty cart
        cart = request.session.get('cart', [])
        
        # add or increment count
        if product_id not in cart:
            cart.append(product_id)
        
        # save cart to session
        request.session['cart'] = cart
        request.session.modified = True
        
        # calculate total items in cart

        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart',
            'cart_count': len(cart)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST # type: ignore
def remove_from_cart(request: HttpRequest) -> HttpResponse:
    """Remove item from cart"""
    try:
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        
        cart = request.session.get('cart', [])
        
        if product_id in cart:
            product = Product.objects.get(id=product_id)
            cart.remove(product_id)
            request.session['cart'] = cart
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'message': f'{product.name} removed from cart',
                'cart_count': len(cart),
            })
        else:
            return JsonResponse({'success': False, 'error': 'Item not in cart'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
@transaction.atomic
def process_payment(request: HttpRequest) -> HttpResponse:
    """Process payment and create orders for PDFs"""
    try:
        data = json.loads(request.body)
        payment_method = data.get('payment_method')
        user_info = data.get('user_info', {})
        
        # validate payment method
        valid_methods = ['stripe', 'paypal', 'bank_transfer']
        if payment_method not in valid_methods:
            return JsonResponse({'success': False, 'error': 'Invalid payment method'})
        
        # get cart from session
        cart_product_ids = request.session.get('cart', [])
        if not cart_product_ids:
            return JsonResponse({'success': False, 'error': 'Cart is empty'})
        
        # get or create user
        email = user_info.get('email')
        if not email:
            return JsonResponse({'success': False, 'error': 'Email is required'})
        
        user = User.objects.get(username=email)
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
            return JsonResponse({'success': False, 'error': 'Email is required'})
        
        # check if user already owns any of these pdfs
        existing_orders = Order.objects.filter(
            user=user,
            product_id__in=cart_product_ids,
            status=True  # successfully purchased
        )
        
        if existing_orders.exists():
            owned_products = [order.product.name for order in existing_orders]
            return JsonResponse({
                'success': False, 
                'error': f'You already own: {", ".join(owned_products)}'
            })
        
        # process payment (simulate for now)
        payment_success = True  # TODO: Integrate with actual payment providers
        
        if not payment_success:
            return JsonResponse({'success': False, 'error': 'Payment failed'})
        
        # create orders for each pdf
        order_ids = []
        for product in Product.get_by_ids(cart_product_ids):
            order = Order(
                product=product,
                user=user,
                price=product.price,
                address='',  # Not needed for digital products
                status=True if payment_method in ['stripe', 'paypal'] else False
            )
            order.placeOrder()
            order_ids.append(order.id)
        
        # clear cart from session
        request.session['cart'] = []
        request.session.modified = True
        
        # TODO: send confirmation email with download links
        
        return JsonResponse({
            'success': True,
            'message': 'Purchase completed successfully! Check your email for download links.',
            'order_ids': order_ids,
            'payment_method': payment_method,
            'redirect_url': '/my-library/'  # redirect to user's purchased PDFs
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def get_cart_count(request: HttpRequest) -> HttpResponse:
    """Get total number of items in cart"""
    cart = request.session.get('cart', [])
    return JsonResponse({'cart_count': len(cart)})


# helper function to clear cart
def clear_cart(request: HttpRequest) -> HttpResponse:
    """Clear all items from cart"""
    request.session['cart'] = []
    request.session.modified = True
    return JsonResponse({'success': True, 'message': 'Cart cleared'})


# Webhook for payment confirmations (if needed)
@csrf_exempt
@require_POST
def payment_webhook(request: HttpRequest) -> HttpResponse:
    """Handle payment webhooks from payment providers"""
    try:
        data = json.loads(request.body)
        
        # TODO: Implement webhook signature verification
        if data.get('type') == 'payment_intent.succeeded':
            # Update order status based on payment reference
            payment_reference = data.get('payment_reference')
            # You'd need to add a payment_reference field to your Order model
            # or use another way to match payments to orders
            
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
