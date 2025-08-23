from django.contrib.auth.views import LogoutView
from django.urls import include, path
from gelv.views import home, catalogue, subscribe, cart, auth, checkout, owned, download
from gelv.admin import admin_site

urlpatterns = [
    # Home page
    path('', home.home_view, name='home'),

    # Authentication
    path('auth/', auth.AuthView.as_view(), name='auth'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('login/', auth.AuthView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # User space
    path('owned/', owned.owned_view, name='owned'),
    path('download/<int:id>/', download.download_view, name='download'),

    # Store
    path('catalogue/', catalogue.catalogue_view, name='catalogue'),
    path('subscribe/', subscribe.subscribe_view, name='subscribe'),

    # Cart & Checkout
    path('cart/', cart.cart_view, name='cart'),
    path('cart/add/', cart.add_to_cart, name='add_to_cart'),
    path('cart/remove/', cart.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', cart.clear_cart, name='clear_cart'),
    path('cart/count/', cart.get_cart_count, name='cart_count'),
    path('checkout/', checkout.process_payment, name='checkout'),

    # Admin/Management
    path('admin/', admin_site.urls),
]
