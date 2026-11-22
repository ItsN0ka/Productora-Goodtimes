from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime, timedelta
from eventos.decorators import administrador_required
from eventos.models import Evento, DetalleEvento, UsoImplemento, Implemento
from .models import SolicitudCotizacion, Cotizacion, DetalleServicioCotizacion, DetalleImplementoCotizacion
from .forms import (
    SolicitudCotizacionForm,
    CotizacionForm,
    DetalleServicioCotizacionForm,
    DetalleImplementoCotizacionForm,
)

#recalcula el total de la cotizacion y la deja en borrador
def _guardar_total_cotizacion(cotizacion):
    cotizacion.precio = cotizacion.calcular_total()
    cotizacion.estado = 'BOR'
    cotizacion.save(update_fields=['precio', 'estado'])

#funcion auxiliar: revisa si la fecha y hora estan libres segun la magnitud
def _fecha_disponible(fecha, hora, magnitud, excluir_pk=None):
    #solo bloquean las solicitudes ya aceptadas de ese mismo dia
    ocupadas = SolicitudCotizacion.objects.filter(fecha=fecha, estado='ACE').exclude(pk=excluir_pk)
    if not ocupadas.exists():
        return True
    #un evento grande ocupa el dia completo
    if magnitud == 'GRA' or ocupadas.filter(magnitud='GRA').exists():
        return False
    #los pequeños y medianos ocupan algunas horas, se revisa que no se crucen
    inicio = datetime.combine(fecha, hora)
    fin = inicio + timedelta(hours=SolicitudCotizacion.HORAS_BLOQUEO[magnitud])
    for otra in ocupadas:
        otra_inicio = datetime.combine(otra.fecha, otra.hora)
        otra_fin = otra_inicio + timedelta(hours=SolicitudCotizacion.HORAS_BLOQUEO[otra.magnitud])
        if inicio < otra_fin and otra_inicio < fin:
            return False
    return True


#COTIZACIONES DEL CLIENTE
@login_required
def crear_cotizacion(request):
    form = SolicitudCotizacionForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            ## que no se pueda poner una fecha pasada a la de hoy
            if form.cleaned_data['fecha'] < timezone.localdate():
                messages.error(request, 'La fecha del evento no puede ser anterior a hoy')
            #que la fecha y hora no choquen con un evento ya aceptado
            elif not _fecha_disponible(form.cleaned_data['fecha'], form.cleaned_data['hora'], form.cleaned_data['magnitud']):
                messages.error(request, 'Esa fecha y hora no está disponible para un evento de esa magnitud.')
            else:
                #se guarda sin enviar a la bd 
                cotizacion = form.save(commit=False)
                cotizacion.cliente = request.user
                cotizacion.save()
                messages.success(request, 'Cotización enviada correctamente.')
                return redirect('mis_cotizaciones')
    #sino se renderiza al formulario de la cotizacion
    return render(request, 'cotizaciones/cliente/cotizacion_form.html', {'form': form, 'accion': 'Solicitar'})

@login_required
def mis_cotizaciones(request):
    #el cliente solo ve sus propias cotizaciones
    cotizaciones = SolicitudCotizacion.objects.filter(cliente=request.user).order_by('-created_at')
    return render(request, 'cotizaciones/cliente/mis_cotizaciones.html', {'cotizaciones': cotizaciones})

@login_required(login_url="iniciar_sesion")
def detalle_cotizacion(request, pk):
    solicitud = get_object_or_404(SolicitudCotizacion, pk=pk, cliente=request.user)
    respuesta = Cotizacion.objects.filter(solicitud=solicitud, estado__in=['ENV', 'ACE', 'REC']).select_related(
        "administrador"
    ).prefetch_related("detalles_servicios__servicio", "detalles_implementos__implemento").first()
    return render(
        request,
        'cotizaciones/cliente/cotizacion_detail.html',
        {'obj': solicitud, 'respuesta': respuesta},
    )


@login_required(login_url='iniciar_sesion')
@transaction.atomic
def aceptar_cotizacion(request, pk):
    if request.method != 'POST':
        return redirect('detalle_cotizacion', pk=pk)

    solicitud = get_object_or_404(
        SolicitudCotizacion.objects.select_for_update(), pk=pk, cliente=request.user
    )
    cotizacion = get_object_or_404(
        Cotizacion.objects.select_for_update().prefetch_related(
            'detalles_servicios__servicio', 'detalles_implementos__implemento'
        ),
        solicitud=solicitud,
    )

    if solicitud.evento_id:
        messages.info(request, 'Esta cotización ya fue convertida en evento.')
        return redirect('detalle_cotizacion', pk=pk)
    if cotizacion.estado != 'ENV':
        messages.info(request, 'Esta cotización ya no está disponible para aceptar.')
        return redirect('detalle_cotizacion', pk=pk)
    if not cotizacion.detalles_servicios.exists() and not cotizacion.detalles_implementos.exists():
        messages.error(request, 'La cotización no tiene servicios ni implementos detallados. Contacta al administrador para que la actualice.')
        return redirect('detalle_cotizacion', pk=pk)
    #que la fecha y hora no hayan sido ocupadas por otro evento aceptado
    if not _fecha_disponible(solicitud.fecha, solicitud.hora, solicitud.magnitud, excluir_pk=solicitud.pk):
        messages.error(request, 'Esa fecha y hora ya fue ocupada por otro evento.')
        return redirect('detalle_cotizacion', pk=pk)

    try:
        with transaction.atomic():
            # Bloquea el stock mientras se valida y crea el evento para evitar 
            # aceptar dos propuestas simultáneamente usando las mismas unidades.
            lineas_implementos = list(cotizacion.detalles_implementos.all())
            list(Implemento.objects.select_for_update().filter(
                pk__in=[linea.implemento_id for linea in lineas_implementos]
            ).order_by('pk'))

            evento = Evento(
                nombre=solicitud.nombre_evento,
                tipo=solicitud.tipo_evento,
                fecha=solicitud.fecha,
                hora=solicitud.hora,
                lugar=solicitud.lugar,
                descripcion=cotizacion.descripcion,
                estado=Evento.Estado.CONFIRMADO,
                cantidad_asistencia=solicitud.cantidad_asistencia,
            )
            evento.full_clean()
            evento.save()

            for linea in cotizacion.detalles_servicios.all():
                DetalleEvento.objects.create(
                    evento=evento,
                    servicio=linea.servicio,
                    precio_acordado=linea.precio_acordado,
                )

            for linea in lineas_implementos:
                uso = UsoImplemento(
                    evento=evento,
                    implemento=linea.implemento,
                    cantidad=linea.cantidad,
                )
                uso.full_clean()
                uso.save()

            solicitud.evento = evento
            solicitud.estado = 'ACE'
            solicitud.save(update_fields=['evento', 'estado'])
            cotizacion.estado = 'ACE'
            cotizacion.save(update_fields=['estado'])
    except ValidationError as error:
        messages.error(request, f'No se pudo aceptar la cotización: {error}')
        return redirect('detalle_cotizacion', pk=pk)

    messages.success(request, 'Cotización aceptada. El evento ya aparece en la vista del administrador.')
    return redirect('detalle_cotizacion', pk=pk)


@login_required
def rechazar_cotizacion(request, pk):
    #buscar la solicitud solo dentro de las del cliente que inicio sesion
    solicitud = get_object_or_404(SolicitudCotizacion, pk=pk, cliente=request.user)
    cotizacion = get_object_or_404(Cotizacion, solicitud=solicitud)
    if request.method == 'POST':
        #solo se puede rechazar una cotizacion enviada
        if cotizacion.estado == 'ENV':
            #se cambia el estado de la cotizacion y de la solicitud
            cotizacion.estado = 'REC'
            cotizacion.save()
            solicitud.estado = 'REC'
            solicitud.save()
            messages.success(request, 'Cotización rechazada correctamente.')
        else:
            #no se puede rechazar porque ya fue aceptada o rechazada
            messages.error(request, 'Esta cotización ya no se puede rechazar.')
    #vuelve al detalle de la cotizacion
    return redirect('detalle_cotizacion', pk=pk)


#PANEL DEL ADMINISTRADOR
@administrador_required
def lista_solicitudes(request):
    #admin ve todas las solicitudes
    solicitudes = SolicitudCotizacion.objects.all().order_by('-created_at')
    return render(request, 'cotizaciones/administrador/solicitudes_list.html', {'solicitudes': solicitudes})


@administrador_required
def responder_solicitud(request, pk):
    solicitud = get_object_or_404(SolicitudCotizacion, pk=pk)
    cotizacion = Cotizacion.objects.filter(solicitud=solicitud).first()
    if solicitud.evento_id or (cotizacion and cotizacion.estado == 'ACE'):
        messages.info(request, 'Esta solicitud ya fue aceptada y convertida en evento.')
        return redirect('lista_eventos')

    if request.method == 'POST' and 'iniciar' in request.POST and cotizacion is None:
        cotizacion = Cotizacion.objects.create(
            solicitud=solicitud,
            administrador=request.user,
            descripcion='',
            precio=Decimal('0.00'),
            estado='BOR',
        )
        messages.success(request, 'Borrador de cotización creado. Ahora puedes agregar sus detalles.')
        return redirect('responder_solicitud', pk=solicitud.pk)

    if cotizacion is not None and request.method == 'POST' and 'guardar_descripcion' in request.POST:
        form = CotizacionForm(request.POST, instance=cotizacion)
        if form.is_valid():
            respuesta = form.save(commit=False)
            respuesta.estado = 'BOR'
            respuesta.save()
            messages.success(request, 'Descripción guardada en el borrador.')
            return redirect('responder_solicitud', pk=solicitud.pk)
    elif cotizacion is not None:
        form = CotizacionForm(instance=cotizacion)
    else:
        form = None

    return render(
        request,
        'cotizaciones/administrador/responder_solicitud.html',
        {
            'form': form,
            'cotizacion': cotizacion,
            'solicitud': solicitud,
            'servicios_cotizados': (
                cotizacion.detalles_servicios.select_related('servicio').all()
                if cotizacion else []
            ),
            'implementos_cotizados': (
                cotizacion.detalles_implementos.select_related('implemento').all()
                if cotizacion else []
            ),
            'form_servicio': DetalleServicioCotizacionForm(),
            'form_implemento': DetalleImplementoCotizacionForm(
                fecha_evento=solicitud.fecha,
            ),
        },
    )


@administrador_required
def agregar_servicio_cotizacion(request, pk):
    cotizacion = get_object_or_404(Cotizacion, solicitud_id=pk)
    if request.method == 'POST' and not cotizacion.solicitud.evento_id:
        form = DetalleServicioCotizacionForm(request.POST)
        if form.is_valid():
            servicio = form.cleaned_data['servicio']
            if cotizacion.detalles_servicios.filter(servicio=servicio).exists():
                messages.error(request, 'Este servicio ya está agregado a la cotización.')
            else:
                linea = form.save(commit=False)
                linea.cotizacion = cotizacion
                linea.save()
                _guardar_total_cotizacion(cotizacion)
                messages.success(request, 'Servicio agregado a la cotización.')
                return redirect('responder_solicitud', pk=pk)
        else:
            messages.error(request, 'Revisa los datos del servicio y su precio.')
    return redirect('responder_solicitud', pk=pk)


@administrador_required
def agregar_implemento_cotizacion(request, pk):
    cotizacion = get_object_or_404(Cotizacion, solicitud_id=pk)
    if request.method == 'POST' and not cotizacion.solicitud.evento_id:
        form = DetalleImplementoCotizacionForm(
            request.POST,
            fecha_evento=cotizacion.solicitud.fecha,
        )
        if form.is_valid():
            implemento = form.cleaned_data['implemento']
            if cotizacion.detalles_implementos.filter(implemento=implemento).exists():
                messages.error(request, 'Este implemento ya está agregado a la cotización.')
            else:
                linea = form.save(commit=False)
                linea.cotizacion = cotizacion
                linea.save()
                _guardar_total_cotizacion(cotizacion)
                messages.success(request, 'Implemento agregado a la cotización.')
                return redirect('responder_solicitud', pk=pk)
        else:
            for errores in form.errors.values():
                for error in errores:
                    messages.error(request, error)
    return redirect('responder_solicitud', pk=pk)


@administrador_required
def editar_detalle_cotizacion(request, pk, tipo, detalle_pk):
    cotizacion = get_object_or_404(Cotizacion, solicitud_id=pk)
    if tipo == 'servicio':
        modelo, clase_form = DetalleServicioCotizacion, DetalleServicioCotizacionForm
    else:
        modelo, clase_form = DetalleImplementoCotizacion, DetalleImplementoCotizacionForm
    detalle = get_object_or_404(modelo, pk=detalle_pk, cotizacion=cotizacion)

    kwargs_form = {}
    if tipo == 'implemento':
        kwargs_form['fecha_evento'] = cotizacion.solicitud.fecha

    if request.method == 'POST' and not cotizacion.solicitud.evento_id:
        form = clase_form(request.POST, instance=detalle, **kwargs_form)
        if form.is_valid():
            campo = 'servicio' if tipo == 'servicio' else 'implemento'
            seleccionado = form.cleaned_data[campo]
            repetido = modelo.objects.filter(
                cotizacion=cotizacion, **{campo: seleccionado}
            ).exclude(pk=detalle.pk).exists()
            if repetido:
                form.add_error(campo, f'Este {campo} ya está agregado a la cotización.')
            else:
                form.save()
                _guardar_total_cotizacion(cotizacion)
                messages.success(request, 'Detalle de la cotización actualizado.')
                return redirect('responder_solicitud', pk=pk)
    else:
        form = clase_form(instance=detalle, **kwargs_form)

    return render(request, 'cotizaciones/administrador/detalle_form.html', {
        'form': form,
        'solicitud': cotizacion.solicitud,
        'tipo': tipo,
    })


@administrador_required
def eliminar_detalle_cotizacion(request, pk, tipo, detalle_pk):
    cotizacion = get_object_or_404(Cotizacion, solicitud_id=pk)
    if tipo not in ('servicio', 'implemento'):
        raise Http404
    modelo = DetalleServicioCotizacion if tipo == 'servicio' else DetalleImplementoCotizacion
    detalle = get_object_or_404(modelo, pk=detalle_pk, cotizacion=cotizacion)
    if cotizacion.solicitud.evento_id:
        messages.error(request, 'No se pueden modificar los detalles de una cotización aceptada.')
        return redirect('responder_solicitud', pk=pk)

    nombre_detalle = (
        detalle.servicio.nombre if tipo == 'servicio' else detalle.implemento.nombre
    )
    if request.method == 'POST':
        detalle.delete()
        _guardar_total_cotizacion(cotizacion)
        messages.success(request, 'Detalle eliminado de la cotización.')
        return redirect('responder_solicitud', pk=pk)

    return render(request, 'cotizaciones/administrador/detalle_delete.html', {
        'cotizacion': cotizacion,
        'solicitud': cotizacion.solicitud,
        'tipo': tipo,
        'nombre_detalle': nombre_detalle,
    })


@administrador_required
def enviar_cotizacion(request, pk):
    cotizacion = get_object_or_404(Cotizacion, solicitud_id=pk)
    if request.method != 'POST' or cotizacion.solicitud.evento_id:
        return redirect('responder_solicitud', pk=pk)
    cotizacion.precio = cotizacion.calcular_total()
    if not cotizacion.detalles_servicios.exists() or cotizacion.precio <= 0:
        messages.error(request, 'Agrega al menos un servicio con precio mayor a cero antes de enviar la cotización.')
        return redirect('responder_solicitud', pk=pk)
    cotizacion.estado = 'ENV'
    cotizacion.save(update_fields=['precio', 'estado'])
    messages.success(request, 'Cotización enviada al cliente.')
    return redirect('lista_eventos')