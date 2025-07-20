from django.urls import path
from . import views
from .views import catalogue, cart, auth, downloads

urlpatterns = [
    # Home page
    path('', views.home, name='home'),
    
    # Authentication
    path('login/', auth.login_view, name='login'),
    path('logout/', auth.logout_view, name='logout'),
    path('register/', auth.register_view, name='register'),
    path('profile/', auth.profile_view, name='profile'),
    
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
    
    # Digital Downloads (PDF-specific)
    path('my-library/', downloads.my_library, name='my_library'),
    # path('download/<int:product_id>/<str:token>/', downloads.secure_download, name='secure_download'),
    # path('redownload/<int:order_id>/', downloads.generate_download_link, name='redownload'),
    
    # Account Management
    path('orders/', views.order_history, name='order_history'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Payment webhooks (if using Stripe/PayPal)
    path('webhooks/payment/', cart.payment_webhook, name='payment_webhook'),
    
    # Admin/Management (if needed)
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
