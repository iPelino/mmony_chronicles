from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.urls import reverse_lazy

from .forms import CustomUserCreationForm, CustomUserLoginForm
from .models import CustomUser

class CustomLoginView(LoginView):
    """
    Custom login view that uses email as the unique identifier
    instead of username.
    """
    form_class = CustomUserLoginForm
    template_name = 'users/login.html'
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    """
    Custom logout view.
    """
    next_page = 'login'

class RegisterView(CreateView):
    """
    View for user registration.
    """
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        """
        If the form is valid, save the associated model and log the user in.
        """
        response = super().form_valid(form)
        # Log the user in after registration
        email = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password1')
        user = authenticate(self.request, username=email, password=password)
        if user is not None:
            login(self.request, user)
            return redirect('dashboard')
        return response

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests: redirect to dashboard if user is already authenticated.
        """
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().get(request, *args, **kwargs)