from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpRequest, HttpResponse
import json
from typing import TypedDict, Any, Callable, Optional, TypeGuard, get_type_hints
from gelv.utils import get_request_content, trace, IssueN
from gelv.models import AbstractProduct, Issue, Subscription, product_types
from gelv.forms import CartSingletonForm


class FieldConfig(TypedDict):
    type: type[Any]
    default: Optional[Callable]


SchemaType = dict[type[AbstractProduct], dict[str, FieldConfig]]


class CartMetadataRegistry:
    def __init__(self) -> None:
        self._schemas: SchemaType = {
            Subscription: {
                'start': {'type': IssueN, 'default': lambda sub: sub.journal.latest_number},
            },
            Issue: {
            }
        }

        self.product_classes: dict[str, type[AbstractProduct]] = {
            'issue': Issue,
            'subscription': Subscription,
        }

    def get_schema(self, product_type):
        return self._schemas.get(product_type, {})

    def create(self, product, **kwargs):
        schema = self.get_schema(type(product))
        metadata = {}

        for field_name, field_config in schema.items():
            if field_name in kwargs:
                if isinstance(kwargs[field_name], field_config['type']):
                    metadata[field_name] = kwargs.pop(field_name)
                else:
                    raise TypeError(f"{field_name} is of type {type(field_name)}, {field_config['type']} expected")
            elif field_config['default']:
                metadata[field_name] = field_config['default'](product)
            else:
                raise AttributeError(f'{field_name} is required for {type(product)}.')

            if kwargs:
                raise AttributeError(f'{kwargs} unexpected for {type(product)}.')

        return metadata


cart_metadata_registry = CartMetadataRegistry()


class CartItem:
    class Raw(TypedDict):
        type: str
        id: int
        metadata: dict[str, Any]

    @classmethod
    def is_raw_dict(cls, data: Any) -> TypeGuard['Raw']:
        raw_T = get_type_hints(cls.Raw)
        return\
            ('type' in data.keys()) and isinstance(data['type'], raw_T['type']) and trace((data['type'] in product_types), 'types') and\
            trace(('id' in data.keys()) and isinstance(data['type'], raw_T['id'])) and\
            trace(isinstance(data.get(['metadata'], {}), raw_T['metadata']))

    product: AbstractProduct
    metadata: dict[str, Any]

    def __init__(self, product: AbstractProduct, **kwargs):
        self.product = product
        self.metadata = cart_metadata_registry.create(product, **kwargs)

    @property
    def metadata_json(self) -> str:
        return json.dumps(self.metadata)

    @classmethod
    def from_singleton_request(cls, request: HttpRequest) -> 'CartItem':
        form = CartSingletonForm(get_request_content(request))
        trace(get_request_content(request))
        if trace(form.is_valid(), 'is valid'):
            data = form.cleaned_data
            trace(data, 'request data')

            product = product_types[data['type']].get_object_or_404(id=data['id'])
            metadata = trace((data.get('metadata', {})), "metadata from singleton")

            return cls(product, **(metadata if metadata else {}))

        else:
            raise TypeError('singleton request of incorrect format.')

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, CartItem):
            raise NotImplementedError
        return (self.product == o.product) and (self.metadata == o.metadata)

    def __str__(self):
        return str(self.product)


class Cart:
    type Raw = list[CartItem.Raw]

    items: list[CartItem]

    def __init__(self, data: Raw):
        trace(data, "generating cart")
        self.items = []
        for item_data in data:
            klass = cart_metadata_registry.product_classes[item_data['type']]
            product = get_object_or_404(klass, id=item_data['id'])
            self.items.append(CartItem(product, **item_data['metadata']))

    @property
    def total_price(self) -> float:
        return sum(i.product.current_price for i in self.items)

    @property
    def raw(self) -> Raw:
        return [{
            'type': type(item.product).__name__.lower(),
            'id': item.product.id,
            'metadata': item.metadata
        } for item in self.items]

    @property
    def issues(self) -> list[CartItem]:
        return self.filter_by_type(Issue)

    @property
    def subscriptions(self) -> list[CartItem]:
        return self.filter_by_type(Subscription)

    def filter_by_type(self, type: type[AbstractProduct]) -> list[CartItem]:
        return list(filter(lambda x: isinstance(x.product, type), self.items))

    def add(self, item: CartItem) -> bool:
        if item not in self.items:
            self.items.append(item)
            return True
        else:
            return False

    def remove(self, item: CartItem) -> bool:
        if item in self.items:
            self.items.remove(item)
            return True
        else:
            return False

    def edit_meta(self, item: CartItem, **kwargs) -> bool:
        trace((item.product, item.metadata), "item to edit")
        for item in self.items:
            trace((item.product, item.metadata), "item in cart")

        if item in self.items:
            ix = self.items.index(item)
            metadata = self.items[ix].metadata
            for field, value in kwargs.items():
                metadata[field] = value
            self.items[ix] = CartItem(item.product, **metadata)
            return True
        else:
            return False

    @classmethod
    def from_session(cls, session: dict) -> 'Cart':
        return Cart(session.get('cart', []))

    def __len__(self):
        len(self.items)

    def __bool__(self):
        return bool(self.items)

    def __str__(self):
        return f'cart with {str(self.items)}'

    @staticmethod
    def get_cart_count(request: HttpRequest) -> HttpResponse:
        """Get total number of items in cart"""
        cart = request.session.get('cart', [])
        return JsonResponse({'cart_count': len(cart)})
