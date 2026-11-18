from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm
from .models import Perfil

# Create your views here.
def iniciar_sesion(request):
    if request.user.is_authenticated:
        return redirect('#')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            Perfil.objects.get_or_create(user=user)
            login(request, user)
            return redirect('#')
    else:
        form =AuthenticationForm(request)
    return render(request, 'registro/iniciar_sesion.html', {'form': form})
