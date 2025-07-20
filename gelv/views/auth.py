# views.py
from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.views.generic import CreateView
from django.views.decorators.csrf import csrf_protect
from django.http import HttpRequest, HttpResponse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from ..models import Product

User = get_user_model()  # type: ignore[misc]


class CustomUserCreationForm(UserCreationForm):
    """
    Custom form for creating users with email authentication
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )

    class Meta:
        model = User
        fields = ("email", "password1", "password2")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # add Bootstrap classes to password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        try:
            validate_email(email)
        except ValidationError:
            raise forms.ValidationError('Please enter a valid email address.')
        return email


class CustomLoginForm(AuthenticationForm):
    """
    Custom login form using email
    """
    username = EmailField(widget=forms.TextInput(attrs={"autofocus": True}))


class CustomLoginView(LoginView):
    """
    Custom login view using email as username
    """
    template_name = 'accounts/login.html'
    form_class = CustomLoginForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('catalogue')
    
    def form_valid(self, form):
        email = form.cleaned_data.get('email').lower().strip()
        password = form.cleaned_data.get('password')
        remember_me = form.cleaned_data.get('remember_me')
        
        # Since we're using email as USERNAME_FIELD, we can authenticate directly with email
        user = authenticate(self.request, email=email, password=password)
        
        if user is not None:
            login(self.request, user)
            
            # Set session expiry based on remember me
            if not remember_me:
                self.request.session.set_expiry(0)  # Session expires when browser closes
            else:
                self.request.session.set_expiry(1209600)  # 2 weeks
            
            messages.success(self.request, f'Welcome back, {user.first_name or user.email}!')
            return super().form_valid(form)
        else:
            form.add_error(None, 'Invalid email or password.')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Login'
        return context


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """
    Dashboard view - requires login
    """
    user = request.user
    
    purchased_products = Product.objects.filter(order__user=user).distinct()
    
    context = {
        'user': user,
        'purchased_products': purchased_products,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    """
    User profile view - requires login
    """
    context = {'user': request.user}
    return render(request, 'accounts/profile.html', context)


# utility function to get user by email
def get_user_by_email(email: str):
    """
    Get user by email (stored in username field)
    """
    try:
        return User.objects.get(username=email.lower())
    except User.DoesNotExist:
        return None
