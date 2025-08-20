from django.core.management.base import BaseCommand
from ...models import Journal, Issue, Subscription
from datetime import date


class Command(BaseCommand):
    def handle(self, *args, **options):
        be_cat = Journal.objects.create(name="Buhgalterija un ekonomika", anno=date(year=2024, month=1, day=1))

        Issue.objects.create(journal=be_cat, number=16, description="BE something", price=0.0)
        Issue.objects.create(journal=be_cat, number=17, description="BE something", price=0.0)
        Issue.objects.create(journal=be_cat, number=18, description="BE something", price=0.0)
        Issue.objects.create(journal=be_cat, number=19, description="BE something", price=0.0)
        Issue.objects.create(journal=be_cat, number=20, description="BE something", price=0.0)
        Issue.objects.create(journal=be_cat, number=21, description="BE something", price=0.0)
        Issue.objects.create(journal=be_cat, number=22, description="BE something", price=0.0)

        Subscription.objects.create(journal=be_cat, duration=3, price=1.0)
        Subscription.objects.create(journal=be_cat, duration=6, price=2.0)
        Subscription.objects.create(journal=be_cat, duration=9, price=3.0)
        Subscription.objects.create(journal=be_cat, duration=12, price=4.0)
