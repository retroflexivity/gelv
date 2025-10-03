from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.files.base import ContentFile
from django.db.models.query import QuerySet
from typing import TypeVar, cast, Optional, get_args, Generator
from django.shortcuts import get_object_or_404
from django.db.models.manager import Manager
from gelv.utils import trace, IssueNumber

P = TypeVar('P', bound='AbstractProduct')


IssueNumberField = models.IntegerField  # starting from 01/2010


class UserManager(BaseUserManager):
    """
    Custom user manager for User model with email as unique identifier.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model that uses email as the unique identifier
    instead of username.
    """
    objects = UserManager()  # type: ignore[assignment, misc]

    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # remove username
    username = None  # type: ignore[assignment]

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def get_owned_issues(self) -> QuerySet['Issue']:
        """Get all issues a user owns, including from subscriptions."""
        issue_orders = IssueOrder.objects.filter(payment__user__id=self.id, payment__paid=True)
        issues = Issue.get_objects(all=True).filter(issueorder__in=issue_orders).distinct()
        sub_orders = SubscriptionOrder.objects.filter(payment__user__id=self.id, payment__paid=True)
        return issues.union(*map(lambda x: x.get_issues(), sub_orders))

    @staticmethod
    def get_by_email(email: str) -> 'User':
        return User.objects.get(email=email)


class Journal(models.Model):
    """
    Journal name or journal for non-journals.
    """
    objects: Manager['Journal']

    name = models.CharField(max_length=200)
    # anno = models.DateField(default=datetime.date(year=2010, month=1, day=1))
    description = models.TextField(default='', blank=True, null=True)
    frequency = models.IntegerField(default=12)

    # def get_issue_number_from_date(self, date: datetime.datetime) -> int:
    #     return diff_month(date, self.anno) + 1  # issues are 1-base numbered

    @property
    def latest_number(self, all=False) -> int:
        return Issue.objects.filter(journal=self.id).aggregate(
            models.Max('number', output_field=models.IntegerField(), default=0)
        )['number__max']

    def get_subscriptions(self, all=False) -> QuerySet['Subscription', 'Subscription']:
        return Subscription.get_objects(all=all).filter(journal=self.id)

    def __str__(self):
        return self.name


class AbstractProduct(models.Model):
    """ Showing 1-7 of 7 items.
    Anything purchasable.
    """
    objects: Manager['AbstractProduct']

    price = models.FloatField(default=0.0)
    discounted_price = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    @property
    def current_price(self):
        return self.discounted_price if self.discounted_price else self.price

    @property
    def formatted_price(self):
        return f'{self.price:.2f} €'

    @property
    def formatted_discounted_price(self):
        return f'{self.discounted_price:.2f} €'

    @classmethod
    def get_objects(cls: type[P], ids: Optional[list[int]] = None, all=False) -> QuerySet['P']:
        id_filter = {'id__in': ids} if (ids is not None) else {}
        active_filter = {} if all else {'is_active': True}
        return cast('QuerySet[P]', cls.objects.filter(**id_filter).filter(**active_filter))

    @classmethod
    def get_object_or_404(cls: type[P], **kwargs) -> P:
        return get_object_or_404(cls, **kwargs)

    class Meta:
        abstract = True


class Issue(AbstractProduct):
    """
    Single issue of a journal.
    """
    objects: Manager['Issue']

    journal = models.ForeignKey(Journal, on_delete=models.CASCADE)
    number = IssueNumberField()
    description = models.TextField(default='', blank=True, null=True)
    file = models.FileField(upload_to='issues')

    @property
    def number_year(self):
        return IssueNumber(self.number, self.journal.frequency)

    def __str__(self):
        return f'{self.journal.name} {str(self.number_year)}'


class Subscription(AbstractProduct):
    """
    Subscription for a journal, of certain duration.
    """
    objects: Manager['Subscription']

    journal = models.ForeignKey(Journal, on_delete=models.CASCADE)
    duration = models.IntegerField()

    def __str__(self):
        return f'{self.journal.name} \u2014 {self.duration}'

    def get_issues(self, start: int) -> QuerySet[Issue]:
        """Get existing issues included in the subscription from a specific date."""
        numbers = range(start, start + self.duration)
        return Issue.get_objects(all=True).filter(journal=self.journal, number__in=numbers)


class Payment(models.Model):
    """
    A single act of purchasing one or more orders,
    used for financial purposes.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)

    paid = models.BooleanField(default=False)
    invoice = models.FileField(upload_to='invoices', null=True)

    comment = models.TextField(null=True)

    # billing details
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    personal_code = models.CharField(max_length=15)
    city = models.CharField(max_length=50)
    address = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    billing_email = models.EmailField()

    def generate_invoice(self):
        from gelv.invoice import Invoice
        invoice = Invoice(self)
        invoice_io = invoice.generate()
        self.invoice.save(invoice.filename, ContentFile(invoice_io.getvalue()), save=True)
        return invoice

    @property
    def total_price(self):
        issue_total = IssueOrder.objects.filter(payment=self).aggregate(models.Sum('price', default=0))['price__sum']
        sub_total = SubscriptionOrder.objects.filter(payment=self).aggregate(models.Sum('price', default=0))['price__sum']
        return issue_total + sub_total

    @property
    def number(self) -> str:
        return f'GK{1000000 + self.id}'

    def __str__(self):
        return self.number

    @property
    def products(self) -> set['AnyProduct']:
        def type_products(order_c: type[AnyOrder]) -> Generator[AnyProduct]:
            return (o.product for o in order_c.objects.filter(payment=self))

        return set().union(*(type_products(order_c) for order_c in get_args(AnyOrder)))

    @classmethod
    def get_latest(cls, user) -> 'Payment':
        """Get latest payment made by a user, if authenticated (for billing details)."""
        try:
            latest = cls.objects.filter(user=user.id).latest('date')
            if not latest.billing_email:
                latest.billing_email = user.email
            return latest
        except (cls.DoesNotExist, AttributeError):
            return cls()


class AbstractOrder(models.Model):
    """
    An atomic purchase of a single product.
    Used for ownership proofing and in invoices.
    """
    objects: models.Manager['AbstractOrder']

    product = models.ForeignKey(AbstractProduct, on_delete=models.CASCADE)
    price = models.FloatField()
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)

    @property
    def invoice_entry(self) -> str:
        return str(self.product)

    def __str__(self) -> str:
        return f'{self.product}'

    @classmethod
    def get_by_user_sorted(cls, user_id: int) -> QuerySet['AbstractOrder']:
        return cls.objects.filter(payment__user=user_id).order_by('-date')

    class Meta:
        abstract = True


class IssueOrder(AbstractOrder):
    """
    Purchase of a single issue.
    Used for ownership proofing and in invoices.
    A user owns any issue iff he has an order with status == True for.
    """
    objects: models.Manager['IssueOrder']
    product = models.ForeignKey(Issue, on_delete=models.CASCADE)


class SubscriptionOrder(AbstractOrder):
    """
    Purchace of a subscription.
    Used for ownership proofing and in invoices.
    A user owns issues that are in range of any of his subscriptions.
    """
    objects: models.Manager['SubscriptionOrder']
    product = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    start = IssueNumberField()

    @property
    def end(self):
        """Last issue of the subscription."""
        return self.start + self.product.duration

    def get_issues(self) -> QuerySet[Issue]:
        """Get existing issues included in the subscription order."""
        return self.product.get_issues(self.start)

    def __str__(self) -> str:
        return f'{self.product} (no {IssueNumber(self.start)} līdz {IssueNumber(self.end)})'


class Post(models.Model):
    """
    A news post to be shown in the feed.
    """
    objects: Manager['Post']

    title = models.TextField()
    description = models.TextField()
    text = models.TextField()
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return self.title


class Ad(models.Model):
    """
    An image to show in the advertisement block.
    """
    name = models.TextField()
    image = models.ImageField(upload_to='ads')
    is_active = models.BooleanField(default=True)

    @classmethod
    def get_active(cls: type['Ad']) -> QuerySet['Ad']:
        return cls.objects.filter(is_active=True)


AnyProduct = Subscription | Issue
AnyOrder = SubscriptionOrder | IssueOrder
product_types: dict[str, type[Issue | Subscription]] = {'issue': Issue, 'subscription': Subscription}
