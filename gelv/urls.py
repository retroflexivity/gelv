from django.contrib.auth.views import LogoutView
from django.conf.urls.static import static
from django.urls import include, path
from gelv.views import catalogue, subscribe, cart, auth, checkout, owned, download, posts
from gelv.admin import admin_site
from gelv.cart import Cart
from gelv.settings import DEBUG, MEDIA_ROOT, MEDIA_URL

urlpatterns = [
    # Home page and news
    path('', posts.PostListView.as_view(), name='home'),
    path('posts', posts.PostListView.as_view(), name='post-list'),
    path('post/<int:pk>/', posts.PostDetailView.as_view(), name='post'),

    # Authentication
    path('accounts/', include('django.contrib.auth.urls')),
    path('auth/', auth.AuthView.as_view(), name='auth'),
    path('login/', auth.AuthView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('confirm-email/<uidb64>/<token>', auth.confirm_registration_view, name='confirm_email'),

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
    path('cart/change_subscription_start/', cart.change_subscription_start, name='change_subscription_start'),
    path('cart/clear/', cart.clear_cart, name='clear_cart'),
    path('cart/count/', Cart.get_cart_count, name='cart_count'),
    path('checkout/', checkout.process_payment, name='checkout'),

    # Admin/Management
    path('admin/', admin_site.urls),
]

urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
