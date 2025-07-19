from django.db import models
from django.db.models.query import QuerySet
from typing import Optional
from typing import TYPE_CHECKING
import datetime

if TYPE_CHECKING:
    from django.db.models.manager import Manager

class Customer(models.Model):
    objects: Manager['Customer']
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=10)
    email = models.EmailField()
    password = models.CharField(max_length=100)

    # to save the data
    def register(self):
        self.save()

    @staticmethod
    def get_customer_by_email(email: str) -> Optional['Customer']:
        try:
            return Customer.objects.get(email=email)
        except Customer.DoesNotExist:
            return None

    def exists(self) -> bool:
        if Customer.objects.filter(email=self.email):
            return True

        return False


class Product(models.Model):
    objects: Manager['Product']

    name = models.CharField(max_length=60)
    price = models.IntegerField(default=0)
    description = models.CharField(
        max_length=250, default='', blank=True, null=True)

    @staticmethod
    def get_products_by_id(ids: list[int]) -> QuerySet['Product']:
        return Product.objects.filter(id__in=ids)

    @staticmethod
    def get_all_products() -> QuerySet['Product']:
        return Product.objects.all()

class Order(models.Model):
    objects: Manager['Order']

    product = models.ForeignKey(Product,
                                on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer,
                                 on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.IntegerField()
    address = models.CharField(max_length=50, default='', blank=True)
    phone = models.CharField(max_length=50, default='', blank=True)
    date = models.DateField(default=datetime.datetime.today)
    status = models.BooleanField(default=False)

    def placeOrder(self) -> None:
        self.save()

    @staticmethod
    def get_orders_by_customer(customer_id: Product) -> QuerySet['Order']:
        return Order.objects.filter(customer=customer_id).order_by('-date')


