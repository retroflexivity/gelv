from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView
from django.urls import reverse_lazy
from . import views
from .views import catalogue, cart, profile

urlpatterns = [
    # Home page
    # path('', views.home, name='home'),
    
    # Authentication
    path('login/', LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True,
        extra_context={'title': 'Login'}
    ), name='login'),
    path('logout/', LogoutView.as_view(
        next_page='login'
    ), name='logout'),
    path('register/', CreateView.as_view(
        form_class=UserCreationForm,
        template_name='registration/register.html',
        success_url=reverse_lazy('login')
    ), name='register'),
    path('profile/', profile.profile_view, name='profile'),    

    # Catalogue
    path('catalogue/', catalogue.catalogue_view, name='catalogue'),
    path('product/<int:product_id>/', catalogue.product_detail_view, name='product_detail'),
    
    # Cart & Checkout
    path('cart/', cart.cart_view, name='cart'),
    path('cart/add/', cart.add_to_cart, name='add_to_cart'),
    path('cart/remove/', cart.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', cart.clear_cart, name='clear_cart'),
    path('cart/count/', cart.get_cart_count, name='cart_count'),
    path('checkout/', cart.process_payment, name='checkout'),
    
    # Admin/Management (if needed)
    # path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
