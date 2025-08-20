from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models import Sum
from django.db.models.query import QuerySet
from typing import TypeVar, cast
import datetime
from dateutil.relativedelta import relativedelta
from gelv.utils import diff_month, trace
from django.db.models.manager import Manager

P = TypeVar('P', bound='AbstractProduct')


def default_prices() -> dict[int, float]:
    return {3: 0.0, 6: 0.0, 9: 0.0, 12: 0.0}


class UserManager(BaseUserManager):
    """
    Custom user manager for User model with email as unique identifier
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
    instead of username
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
        issues = Issue.objects.filter(issueorder__payment__user_id=self.id)
        sub_orders = SubscriptionOrder.objects.filter(payment__user__id=self.id)
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
    anno = models.DateField(default=datetime.date(year=2010, month=1, day=1))
    description = models.TextField(default='', blank=True, null=True)

    def get_issue_number_from_date(self, date: datetime.datetime) -> int:
        return diff_month(date, self.anno) + 1  # issues are 1-base numbered

    def __str__(self):
        return self.name


class AbstractProduct(models.Model):
    """
    Anything purchasable.
    """
    objects: Manager['AbstractProduct']

    id = models.AutoField(primary_key=True)

    journal = models.ForeignKey(Journal, on_delete=models.CASCADE)
    price = models.FloatField(default=0.0)

    @classmethod
    def get_by_ids(cls: type[P], ids: list[int]) -> QuerySet['P']:
        return cast('QuerySet[P]', cls.objects.filter(id__in=ids))

    class Meta:
        abstract = True


class Issue(AbstractProduct):
    """
    Single issue of a journal.
    """
    objects: Manager['Issue']

    journal = models.ForeignKey(Journal, on_delete=models.CASCADE)
    number = models.IntegerField()
    description = models.TextField(default='', blank=True, null=True)

    def __str__(self):
        date = self.journal.anno + relativedelta(months=self.number - 1)
        return f'{self.journal.name} {date.month}/{date.year}'


class Subscription(AbstractProduct):
    """
    Subscription for a journal, of certain duration.
    """
    objects: Manager['Subscription']

    journal = models.ForeignKey(Journal, on_delete=models.CASCADE)
    duration = models.IntegerField()

    def __str__(self):
        return f'{self.journal.name} \u2014 {self.duration}'

    def get_issues(self, start) -> QuerySet[Issue]:
        """Get existing issues included in the subscription from a specific date"""
        start_number = self.journal.get_issue_number_from_date(start)
        numbers = range(start_number, start_number + self.duration)
        return Issue.objects.filter(journal=self.journal, number__in=numbers)


class Payment(models.Model):
    """
    A single act of purchasing one or more orders,
    used for financial purposes.
    """
    id = models.AutoField(primary_key=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)

    def get_total_price(self):
        issue_total = IssueOrder.filter(payment=self).aggregate(Sum("price"))
        sub_total = SubscriptionOrder.filter(payment=self).aggregate(Sum("price"))
        return issue_total + sub_total

    @classmethod
    def new(cls, user: User) -> 'Payment':
        payment = cls(
            user=user
        )
        payment.save()
        return payment


class AbstractOrder(models.Model):
    """
    An atomic purchase of a single product.
    """
    objects: models.Manager['AbstractOrder']
    id = models.AutoField(primary_key=True)

    product = models.ForeignKey(AbstractProduct, on_delete=models.CASCADE)
    price = models.IntegerField()
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)

    @classmethod
    def get_by_user_sorted(cls, user_id: int) -> QuerySet['AbstractOrder']:
        return cls.objects.filter(payment__user=user_id).order_by('-date')

    @classmethod
    def new(cls, product: AbstractProduct, payment: Payment) -> 'AbstractOrder':
        order = cls(
            product=product,
            price=product.price,
            payment=payment
        )
        order.save()
        return order

    class Meta:
        abstract = True


class IssueOrder(AbstractOrder):
    """
    Purchase of a single issue. A user owns any issue
    he has an order with status == True for.
    """
    product = models.ForeignKey(Issue, on_delete=models.CASCADE)


class SubscriptionOrder(AbstractOrder):
    """
    Purchace of a subscription. A user owns any issue
    that is in range of any of his subscriptions.
    """
    product = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    starts = models.DateField(default=timezone.now()
                              .replace(day=1))

    def get_issues(self) -> QuerySet[Issue]:
        """Get existing issues included in the subscription order."""
        return self.product.get_issues(self.starts)
