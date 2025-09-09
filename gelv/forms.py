from json import loads, JSONDecodeError
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from gelv.models import product_types
from gelv.utils import trace

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'})
    )

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class CartSingletonForm(forms.Form):
    id = forms.IntegerField()
    type = forms.ChoiceField(choices=product_types.items())
    metadata = forms.JSONField(required=False)

    def clean(self):
        trace(self.data, 'form data')
        cleaned = super().clean()
        trace(cleaned, 'cleaned')
        trace(self.is_valid(), 'is valid')
        return cleaned
