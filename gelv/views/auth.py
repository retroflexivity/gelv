# views.py
from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic import CreateView
from django.views.decorators.csrf import csrf_protect
from django.http import HttpRequest, HttpResponse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from ..models import Product


class EmailUserCreationForm(UserCreationForm):
    """
    Custom form that uses email instead of username
    """
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ("email", "password1", "password2")
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email'].lower()  # Store email in username field
        user.email = self.cleaned_data['email'].lower()     # Also store in email field
        if commit:
            user.save()
        return user

@csrf_protect
def login_view(request: HttpRequest) -> HttpResponse:
    """
    Handle user login using email as username
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        
        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return render(request, 'accounts/login.html')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.email}!')
            
            # Redirect to next page or dashboard
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'accounts/login.html')


def logout_view(request: HttpRequest) -> HttpResponse:
    """
    Handle user logout
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


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
