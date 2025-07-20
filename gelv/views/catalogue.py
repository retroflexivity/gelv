from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponse
from django.http.request import HttpRequest
from django.db.models import Q, Count
from ..models import Product, Category, User, Order


def catalogue_view(request: HttpRequest) -> HttpResponse:
    """Main catalogue view with filtering and search"""
    
    # get filter parameters
    category_id = request.GET.get('category', '')
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'name')  # name, price_low, price_high, newest
    page = request.GET.get('page', 1)
    
    filters = Q()
    # category filter
    if category_id:
        try:
            filters &= Q(category_id=int(category_id))
        except (ValueError, TypeError):
            pass

    # search filter
    if search_query:
        filters &= (
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # sorting
    order_by = {
        'price_low': 'price',
        'price_high': '-price', 
        'newest': '-id',
        'name': 'name'
    }.get(sort_by, 'name')

    products = Product.objects.filter(filters).order_by(order_by)

    # get all categories for filter dropdown + product number
    categories = Category.objects.all().annotate(product_count=Count('product'))
    
    # pagination
    paginator = Paginator(products, 20)  # show 20 products per page
    try:
        page_products = paginator.page(page)
    except PageNotAnInteger:
        page_products = paginator.page(1)
    except EmptyPage:
        page_products = paginator.page(paginator.num_pages)
    
    # Get user's owned products if logged in
    owned_product_ids = []
    if request.user.is_authenticated:
        try:
            user = User.objects.get(username=request.user.email)
            if user:
                owned_product_ids = list(Order.objects.filter(
                    user=user,
                    status=True
                ).values_list('product_id', flat=True))
        except (ObjectDoesNotExist, AttributeError):
            pass
    
    # Get current cart items
    cart_items = request.session.get('cart', [])
    
    context = {
        'products': page_products,
        'categories': categories,
        'current_category': int(category_id) if category_id else None,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_products': paginator.count,
        'owned_product_ids': owned_product_ids,
        'cart_items': cart_items,
        'sort_options': [
            {'value': 'name', 'label': 'Name (A-Z)'},
            {'value': 'price_low', 'label': 'Price (Low to High)'},
            {'value': 'price_high', 'label': 'Price (High to Low)'},
            {'value': 'newest', 'label': 'Newest First'},
        ]
    }
    
    return render(request, 'catalogue/catalogue.html', context)


def product_detail_view(request: HttpRequest, product_id: int) -> HttpResponse:
    """Individual product detail page"""
    
    product = get_object_or_404(Product, id=product_id)
    
    # get related products from same category
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product_id)[:4]
    
    # check if user owns this product
    user_owns_product = False
    if request.user.is_authenticated:
        try:
            user = User.objects.get(username=request.user.email)
            if user:
                user_owns_product = Order.objects.filter(
                    user=user,
                    product=product,
                    status=True
                ).exists()
        except (ObjectDoesNotExist, AttributeError):
            pass
    
    # check if product is in cart
    cart_items = request.session.get('cart', [])
    in_cart = product.id in cart_items
    
    context = {
        'product': product,
        'related_products': related_products,
        'user_owns_product': user_owns_product,
        'in_cart': in_cart,
    }
    
    return render(request, 'catalogue/product_detail.html', context)
