from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from gelv.invoice import Invoice
from gelv.variables import site_url
from gelv.utils import get_request_content, trace
from gelv.views.cart import Cart, PAYMENT_METHODS, BILLING_DETAILS_FIELDS
from gelv.models import Issue, Subscription, IssueOrder, SubscriptionOrder, User, Payment


def send_invoice_mail(user: User, invoice: Invoice) -> bool:

    site_name = getattr(settings, 'SITE_NAME', None)
    context = {
        'user': user,
        'invoice': invoice,
        'site_name': site_name,
        'owned_url': site_url + reverse('owned')
    }

    try:
        msg = EmailMessage(
            to=(user.email,),
            subject=f'Your {site_name} invoice {invoice.number}',
            body=render_to_string('emails/invoice_email.txt', context),
            from_email=settings.DEFAULT_FROM_EMAIL,
        )
        msg.attach_file(invoice.filepath)
        msg.send()

        trace(user.email, f'invoice email for {invoice.number} (payment {invoice.payment.id}) sent to:')
        return True
    except Exception as e:
        trace(e, f'send email for invoice {invoice.number} (payment {invoice.payment.id}) failed:')
        return False


@require_POST
@transaction.atomic
def process_payment(request: HttpRequest) -> HttpResponse:
    """Process payment and create orders"""
    print("init payment")
    data = get_request_content(request)
    payment_method = data.get('payment_method')
    email = data.get('email')
    billing_details = {field['id']: data.get(field['id']) for field in BILLING_DETAILS_FIELDS}

    cart = Cart.from_session(request.session)
    if not cart:
        messages.error(request, 'Cart is empty')
        return redirect(request.META.get('HTTP_REFERER', 'catalogue'))

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

    trace(type(cart.issues))
    # check if user already owns any of the issues
    owned = user.get_owned_issues().filter(
        pk__in=[issue.product.id for issue in cart.issues],
    )

    if owned.exists():
        messages.error(request, f'You already own {", ".join(map(str, owned))}.')
        return redirect(request.META.get('HTTP_REFERER', 'cart'))

    # create a single Payment and Orders for each product
    payment = Payment.objects.create(user=user, **billing_details)

    # TODO: make it declarative in the Cart class
    for sub in cart.subscriptions:
        if isinstance(sub.product, Subscription):
            SubscriptionOrder.objects.create(product=sub.product, payment=payment, price=sub.product.current_price, **sub.metadata)
    for issue in cart.issues:
        if isinstance(issue.product, Issue):
            IssueOrder.objects.create(product=issue.product, payment=payment, price=issue.product.current_price, **issue.metadata)

    # generate and send invoice
    invoice = Invoice(payment)
    invoice.generate()
    success = send_invoice_mail(user, invoice)
    if success:
        messages.success(request, 'Order completed! Please check your inbox for an invoice.')
    else:
        messages.error(request, 'Order completed! But we couldn\'t send you an invoice. You can find it in the Account tab under "payments".')

    # save billing details to the user
    for attr, value in billing_details.items():
        setattr(user, attr, value)
    user.save()

    # clear cart from session
    request.session['cart'] = []
    request.session.modified = True
    return redirect('home')
