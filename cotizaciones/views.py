from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import SolicitudCotizacion
from .forms import SolicitudCotizacionForm
##cotiaciones del cliente
@login_required
def crear_cotizacion(request):
    form = SolicitudCotizacionForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            ## que no se pueda poner una fecha pasada a la de hoy
            if form.cleaned_data['fecha'] < timezone.localdate():
                messages.error(request, 'La fecha del evento no puede ser anterior a hoy')
            else:
                #se guarda sin enviar a la bd 
                cotizacion = form.save(commit=False)
                cotizacion.cliente = request.user
                cotizacion.save()
                messages.success(request, 'Cotización enviada correctamente.')
                return redirect('mis_cotizaciones')
    #sino se renderiza al formulario de la cotizacion
    return render(request, 'cotizaciones/cotizacion_form.html', {'form': form, 'accion': 'Solicitar'})

@login_required
def mis_cotizaciones(request):
    #el cliente solo ve sus propias cotizaciones
    cotizaciones = SolicitudCotizacion.objects.filter(cliente=request.user).order_by('-created_at')
    return render(request, 'cotizaciones/mis_cotizaciones.html', {'cotizaciones': cotizaciones})

@login_required
def detalle_cotizacion(request, pk):
    #buscar la cotizacion solo dentro de las del cliente, si no existe muestra error 404
    cotizacion = get_object_or_404(SolicitudCotizacion, pk=pk, cliente=request.user)
    return render(request, 'cotizaciones/cotizacion_detail.html', {'obj': cotizacion})