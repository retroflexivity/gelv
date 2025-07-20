from django.db import models
from django.contrib.auth.models import AbstractUser,UserManager
from django.db.models.query import QuerySet
from typing import Optional
from typing import TYPE_CHECKING
import datetime

if TYPE_CHECKING:
    from django.db.models.manager import Manager


class User(AbstractUser):
    """
    Custom user model that uses email as the unique identifier
    instead of username.
    """
    objects: UserManager['User']
    
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Remove username requirement
    username = None
    
    USERNAME_FIELD = 'email'
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class Category(models.Model):
    objects: Manager['Category']
    
    name = models.CharField(max_length=200)


class Product(models.Model):
    objects: Manager['Product']

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    price = models.IntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    description = models.CharField(
        max_length=20000, default='', blank=True, null=True)

    @staticmethod
    def get_by_ids(ids: list[int]) -> QuerySet['Product']:
        return Product.objects.filter(id__in=ids)


class Order(models.Model):
    objects: models.Manager['Order']
    id = models.AutoField(primary_key=True)

    product = models.ForeignKey(Product,
                                on_delete=models.CASCADE)
    user = models.ForeignKey(User,
                                 on_delete=models.CASCADE)
    price = models.IntegerField()
    address = models.CharField(max_length=50, default='', blank=True)
    phone = models.CharField(max_length=50, default='', blank=True)
    date = models.DateField(default=datetime.datetime.today)
    status = models.BooleanField(default=False)

    def placeOrder(self) -> None:
        self.save()

    @staticmethod
    def get_by_user_sorted(user_id: int) -> QuerySet['Order']:
        return Order.objects.filter(user=user_id).order_by('-date')
