from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from registro.models import Perfil


def administrador_required(view_func):
    

    @login_required(login_url="iniciar_sesion")
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        es_administrador = Perfil.objects.filter(
            user=request.user,
            rol__nombre="Administrador",
        ).exists()

        if not es_administrador:
            return render(
                request,
                "registro/acceso_restringido.html",
                status=403,
            )

        return view_func(request, *args, **kwargs)

    return wrapped_view
