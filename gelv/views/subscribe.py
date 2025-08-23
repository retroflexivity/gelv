from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import AnonymousUser
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponse
from django.http.request import HttpRequest
from django.db.models import Q, Count
from typing import List
from ..models import Subscription, User, SubscriptionOrder, Journal


def get_user_subs(user: User | AnonymousUser) -> List[int]:
    try:
        if user.is_authenticated:
            user = User.get_by_email(user.email)
            if user:
                return list(SubscriptionOrder.objects.filter(
                    payment__user=user,
                ).values_list('product_id', flat=True))
        return []
    except (ObjectDoesNotExist, AttributeError):
        return []


def subscribe_view(request: HttpRequest) -> HttpResponse:
    """Subscription page view"""

    journals = Journal.objects.annotate(sub_count=Count('subscription')).filter(sub_count__gt=0)

    print(journals[0].get_subscriptions())

    context = {
        'journals': journals,
        'owned_subscription_ids': get_user_subs(request.user),
    }

    return render(request, 'subscribe/subscribe.html', context)
