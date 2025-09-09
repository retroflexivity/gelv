from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.views import View
from gelv.utils import trace, smart_redirect
from gelv.forms import CustomUserCreationForm
from gelv.models import User


def send_confirm_mail(user: User, request=None) -> bool:
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    if request:
        current_site = get_current_site(request)
        domain = current_site.domain
        protocol = 'https' if request.is_secure() else 'http'
    else:
        # fallback if no request available
        domain = getattr(settings, 'SITE_DOMAIN', 'localhost:8000')
        protocol = getattr(settings, 'SITE_PROTOCOL', 'http')

    confirmation_url = f"{protocol}://{domain}{reverse('confirm_email', kwargs={'uidb64': uid, 'token': token})}"

    site_name = getattr(settings, 'SITE_NAME', None)
    context = {
        'user': user,
        'confirmation_url': confirmation_url,
        'site_name': site_name,
    }

    try:
        send_mail(
            recipient_list=[user.email],
            subject=f'Confirm your {site_name} email address',
            message=render_to_string('emails/confirmation_email.txt', context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            # html_message=render_to_string('emails/confirmation_email.html', context),
            fail_silently=False,
        )

        trace(f'confirmation email sent to {user.email}')
        return True
    except Exception as e:
        trace(e)
        return False


def confirm_registration_view(request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
    """
    Activate the user after following a confirmation link.
    """

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        assert default_token_generator.check_token(user, token)

        user.is_active = True
        user.save()

    except (TypeError, ValueError, OverflowError, User.DoesNotExist, AssertionError):
        messages.error(request, 'The confirmation link is invalid or has expired.')

    return smart_redirect(request, 'home')


class AuthView(View):
    template_name = 'registration/auth.html'

    def get(self, request):
        # If user is already logged in, redirect them
        if request.user.is_authenticated:
            return redirect('catalogue')

        print('getting')
        login_form = AuthenticationForm()
        signup_form = CustomUserCreationForm()

        return render(request, self.template_name, {
            'login_form': login_form,
            'signup_form': signup_form,
        })

    def post(self, request):
        if 'login_submit' in request.POST:
            return self.handle_login(request)
        elif 'signup_submit' in request.POST:
            return self.handle_signup(request)
        else:
            return redirect('auth')

    def handle_login(self, request):
        login_form = AuthenticationForm(data=request.POST)
        signup_form = CustomUserCreationForm()

        if login_form.is_valid():
            print("logging in")
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, 'Successfully logged in!')
                return redirect('catalogue')
            else:
                messages.error(request, 'You are already logged in.')

        else:
            messages.error(request, 'Invalid email or password.')

        return render(request, self.template_name, {
            'login_form': login_form,
            'signup_form': signup_form,
        })

    def handle_signup(self, request):
        login_form = AuthenticationForm()
        signup_form = CustomUserCreationForm(request.POST)

        if signup_form.is_valid():
            user = signup_form.save()
            trace(f'signing up as {user}')
            # login(request, user)
            if send_confirm_mail(user, request):
                messages.success(request, 'Account created successfully! Please check your inbox for a confirmation link.')
            else:
                messages.error(request, 'We couldn\'t send you a confirmation link. Please try again or contact us.')
            return smart_redirect(request, 'catalogue')
        else:
            trace(signup_form)

        return render(request, self.template_name, {
            'login_form': login_form,
            'signup_form': signup_form,
        })
