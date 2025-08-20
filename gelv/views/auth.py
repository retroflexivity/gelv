from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views import View
from ..forms import CustomUserCreationForm


class AuthView(View):
    template_name = 'registration/auth.html'

    def get(self, request):
        # If user is already logged in, redirect them
        if request.user.is_authenticated:
            return redirect('catalogue')

        print('getting')
        login_form = AuthenticationForm()
        signup_form = CustomUserCreationForm()

        return render(request, self.template_name, {
            'login_form': login_form,
            'signup_form': signup_form,
        })

    def post(self, request):
        if 'login_submit' in request.POST:
            return self.handle_login(request)
        elif 'signup_submit' in request.POST:
            return self.handle_signup(request)
        else:
            return redirect('auth')

    def handle_login(self, request):
        login_form = AuthenticationForm(data=request.POST)
        signup_form = CustomUserCreationForm()

        if login_form.is_valid():
            print("logging in")
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, 'Successfully logged in!')
                return redirect('catalogue')
            else:
                messages.error(request, 'You are already logged in.')

        else:
            messages.error(request, 'Invalid email or password.')

        return render(request, self.template_name, {
            'login_form': login_form,
            'signup_form': signup_form,
        })

    def handle_signup(self, request):
        print("signing up")
        login_form = AuthenticationForm()
        signup_form = CustomUserCreationForm(request.POST)

        if signup_form.is_valid():
            user = signup_form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')

        return render(request, self.template_name, {
            'login_form': login_form,
            'signup_form': signup_form,
        })
