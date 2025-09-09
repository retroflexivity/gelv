from django.core.management.base import BaseCommand
from ...models import Journal, Issue, Subscription
from datetime import date


class Command(BaseCommand):
    def handle(self, *args, **options):
        be_cat = Journal.objects.create(name="Buhgalterija un ekonomika")
        be_cat = Journal.objects.create(name="Gramatvedības prakse")

        Issue.objects.create(journal=be_cat, number=184, description="BE something", price=1.0)
        Issue.objects.create(journal=be_cat, number=185, description="BE something", price=1.0)
        Issue.objects.create(journal=be_cat, number=186, description="BE something", price=1.0)
        Issue.objects.create(journal=be_cat, number=187, description="BE something", price=1.0)
        Issue.objects.create(journal=be_cat, number=188, description="BE something", price=1.0)
        Issue.objects.create(journal=be_cat, number=189, description="BE something", price=1.0)
        Issue.objects.create(journal=be_cat, number=190, description="BE something", price=1.0)

        Subscription.objects.create(journal=be_cat, duration=3, price=1.0)
        Subscription.objects.create(journal=be_cat, duration=6, price=2.0)
        Subscription.objects.create(journal=be_cat, duration=9, price=3.0)
        Subscription.objects.create(journal=be_cat, duration=12, price=4.0)
