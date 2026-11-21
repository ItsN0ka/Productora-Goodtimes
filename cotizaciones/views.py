from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import SolicitudCotizacion, Cotizacion
from .forms import SolicitudCotizacionForm, CotizacionForm
from eventos.decorators import administrador_required
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


#PANEL DEL ADMINISTRADOR
#solo usuarios con rol administrador
@administrador_required
def lista_solicitudes(request):
    #el administrador ve todas las solicitudes de todos los clientes
    solicitudes = SolicitudCotizacion.objects.all().order_by('-created_at')
    return render(request, 'cotizaciones/solicitudes_list.html', {'solicitudes': solicitudes})

@administrador_required
def preparar_cotizacion(request, pk):
    solicitud = get_object_or_404(SolicitudCotizacion, pk=pk)
    #cada solicitud tiene una sola cotizacion
    if hasattr(solicitud, 'cotizacion'):
        messages.warning(request, 'Esta solicitud ya tiene una cotización.')
        return redirect('lista_solicitudes')
    form = CotizacionForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            #se asigna la solicitud y el administrador que inicio sesion
            cotizacion = form.save(commit=False)
            cotizacion.solicitud = solicitud
            cotizacion.administrador = request.user
            cotizacion.save()
            #la solicitud queda aceptada porque ya tiene su cotizacion
            solicitud.estado = 'ACE'
            solicitud.save()
            messages.success(request, 'Cotización enviada al cliente.')
            return redirect('lista_solicitudes')
    #sino se renderiza al formulario de la cotizacion
    return render(request, 'cotizaciones/cotizacion_admin_form.html', {'form': form, 'obj': solicitud})
