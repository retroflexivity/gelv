from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.query import QuerySet
from typing import Optional, TYPE_CHECKING
import datetime

from django.db.models.manager import Manager


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
    
    @staticmethod
    def get_by_email(email: str) -> 'User':
        return User.objects.get(email=email)


class Category(models.Model):
    objects: Manager['Category']
    
    name = models.CharField(max_length=200)


class Product(models.Model):
    objects: Manager['Product']

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    price = models.FloatField(default=0.0)
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
