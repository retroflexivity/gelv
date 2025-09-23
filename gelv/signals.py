# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from gelv.models import Payment
from gelv.invoice import Invoice


@receiver(post_save, sender=Payment)
def send_payment_confirmation_email(sender, instance, created, update_fields, **kwargs):
    """
    Send an email when a payment's paid field is changed from False to True.
    """
    if not created and instance.paid and (update_fields is None or 'paid' in update_fields):
        context = {
            'user': instance.user,
            'payment_number': Invoice(instance).number,
            'site_name': getattr(settings, 'SITE_NAME', None)
        }

        send_mail(
            subject='Payment confirmed',
            message=render_to_string('emails/paid_email.txt', context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.user.email],
            fail_silently=False,
        )
