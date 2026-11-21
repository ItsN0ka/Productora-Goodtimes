from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm
from .models import Perfil

def iniciar_sesion(request):
    if request.user.is_authenticated:
        if Perfil.objects.filter(user=request.user, rol__nombre='Administrador').exists():
            return redirect('lista_eventos')
        return redirect('acceso_restringido')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.getuser()
            perfil,  = Perfil.objects.get_or_create(user=user)
            login(request, user)
            if perfil.rol.nombre == 'Administrador':
                return redirect('lista_eventos')
            return redirect('acceso_restringido')
    else:
        form =AuthenticationForm(request)
    return render(request, 'registro/iniciar_sesion.html', {'form': form})

@login_required(login_url='iniciar_sesion')
def acceso_restringido(request):
    return render(request, 'registro/acceso_restringido.html', status=403)

def registrar_usuario(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('iniciar_sesion')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registro/registrar_usuario.html', {'form': form})

def cerrar_sesion(request):
    logout(request)
    return redirect('iniciar_sesion')