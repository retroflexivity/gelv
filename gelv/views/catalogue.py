from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet
from django.http.response import HttpResponse
from django.http.request import HttpRequest
from django.db.models import Q, Count
from ..models import Issue, Journal, IssueOrder, User
from ..utils import trace


def catalogue_view(request: HttpRequest) -> HttpResponse:
    """Main catalogue view with filtering and search"""

    # get filter parameters
    journal_id = request.GET.get('journal', '')
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'name')  # name, price_low, price_high, newest
    page = request.GET.get('page', 1)

    filters = Q()
    # journal filter
    if journal_id:
        try:
            filters &= Q(journal_id=int(journal_id))
        except (ValueError, TypeError):
            pass

    # search filter
    # TODO: make it work with issue numbers
    if search_query:
        filters &= (
            Q(journal__name__icontains=search_query) | Q(description__icontains=search_query)
        )

    # sorting
    order_by = {
        'price_low': 'price',
        'price_high': '-price',
        'newest': '-id',
        'name': 'journal__name'
    }.get(sort_by, 'name')

    products = Issue.get_objects().filter(filters).order_by(order_by)

    # get all journals for filter dropdown + product number
    journals = Journal.objects.all().annotate(issue_count=Count('issue'))

    # pagination
    paginator = Paginator(products, 20)
    try:
        page_products = paginator.page(page)
    except PageNotAnInteger:
        page_products = paginator.page(1)
    except EmptyPage:
        page_products = paginator.page(paginator.num_pages)

    # Get user's owned products if logged in
    owned_product_ids: QuerySet[Issue, int] = QuerySet()
    if request.user.is_authenticated:
        try:
            user = User.get_by_email(request.user.email)
            if user:
                owned_product_ids = user.get_owned_issues().values_list('id', flat=True)
        except ObjectDoesNotExist as e:
            trace(e)

    # Get issues in cart
    cart_items = [id for kind, id in request.session.get('cart', []) if kind == 'issue']

    context = {
        'products': page_products,
        'journals': journals,
        'current_journal': int(journal_id) if journal_id else None,
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
