from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import ProtectedError
from django.db.models import Sum
from .models import Evento, DetalleEvento, UsoImplemento, ParticipacionTrabajador, FeedbackTrabajador
from .forms import (
    EventoForm,
    DetalleEventoForm,
    EditarDetalleEventoForm,
    UsoImplemtosForm,
    EditarUsoImplementoForm,
    ParticipacionTrabajadorForm,
    EditarParticipacionTrabajadorForm,
    FeedbackTrabajadorForm,
)
from registro.models import Perfil
from .decorators import administrador_required

# Create your views here.
#Evento
@administrador_required
def lista_eventos(request):
    eventos = Evento.objects.order_by("fecha")
    return render(request, "eventos/evento/evento_list.html", {"eventos": eventos})

@administrador_required
def crear_evento(request):
    if request.method == "POST":
        form = EventoForm(request.POST)
        if form.is_valid():
            evento = form.save()
            messages.success(request, "Evento creado correctamente.")
            return redirect("detalle_eventos", pk=evento.pk)
    else:
        form = EventoForm()
    return render(request, "eventos/evento/evento_form.html", {"form": form})

@administrador_required
def eliminar_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == "POST":
        try:
            evento.delete()
            messages.success(request, "El evento se eliminó correctamente.")
            return redirect("lista_eventos")
        except ProtectedError:
            messages.error(request, "No se puede eliminar este evento porque tiene datos relacionados.")
            return redirect("detalle_eventos", pk=evento.pk)
    return render(request, "eventos/evento/evento_delete.html", {"evento": evento})

@administrador_required
def detalle_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    return mostrar_detalle_evento(request, evento)


@administrador_required
def resumen_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    servicios = evento.servicios.select_related("servicio")
    total = servicios.aggregate(total=Sum("precio_acordado"))["total"] or 0

    contexto = {
        "evento": evento,
        "servicios_evento": servicios,
        "implementos_evento": evento.implementos_usados.select_related("implemento"),
        "participaciones_trabajador": evento.participaciones.select_related(
            "trabajador", "feedback"
        ),
        "precio_total": total,
    }
    return render(request, "eventos/evento/evento_resumen.html", contexto)


@administrador_required
def lista_resumenes_eventos(request):
    eventos = Evento.objects.order_by("fecha", "nombre")
    return render(
        request,
        "eventos/evento/evento_resumen_list.html",
        {"eventos": eventos},
    )

@administrador_required
def editar_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)

    if request.method == "POST":
        form = EventoForm(request.POST, instance=evento)

        if form.is_valid():
            form.save()
            messages.success(request, "Evento actualizado correctamente.")
            return redirect("detalle_eventos", pk=evento.pk)
    else:
        form = EventoForm(instance=evento)

    return render(request, "eventos/evento/evento_form.html", {"form": form, "evento": evento})

def mostrar_detalle_evento(request, evento, form_servicio=None, form_implemento=None, form_trabajador=None,):
    contexto = {
        "evento": evento,
        "es_administrador": (
            request.user.is_authenticated
            and Perfil.objects.filter(
                user=request.user,
                rol__nombre="Administrador",
            ).exists()
        ),
        "servicios_evento": evento.servicios.select_related("servicio"),
        "implementos_evento": evento.implementos_usados.select_related("implemento"),
        "participaciones_trabajador": evento.participaciones.select_related(
            "trabajador", "feedback"
        ),
        "form_servicio": (
            form_servicio if form_servicio is not None 
            else DetalleEventoForm()
        ),
        "form_implemento": (
            form_implemento if form_implemento is not None 
            else UsoImplemtosForm(evento=evento)
        ),
        "form_trabajador": (
            form_trabajador if form_trabajador is not None
            else ParticipacionTrabajadorForm()
        ),
    }

    return render(request,"eventos/evento/evento_detail.html", contexto)

@administrador_required
def agregar_servicio_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)

    if request.method != "POST":
        return redirect("detalle_eventos", pk=pk)

    form = DetalleEventoForm(request.POST)

    if form.is_valid():
        servicio = form.cleaned_data["servicio"]

        if DetalleEvento.objects.filter(evento=evento, servicio=servicio).exists():
            form.add_error("servicio", "Este servicio ya está agregado al evento.")
        else:
            detalle = form.save(commit=False)
            detalle.evento = evento
            detalle.save()

            messages.success(request, "Servicio agregado al evento.")
            return redirect("detalle_eventos", pk=pk)
    return mostrar_detalle_evento(request, evento, form_servicio=form)


@administrador_required
def eliminar_servicio_evento(request, pk, detalle_pk):
    evento = get_object_or_404(Evento, pk=pk)
    detalle = get_object_or_404(DetalleEvento, pk=detalle_pk, evento=evento)

    if request.method == "POST":
        detalle.delete()
        messages.success(request, "Servicio quitado del evento.")
        return redirect("detalle_eventos", pk=evento.pk)

    return render(
        request,
        "eventos/servicios/servicio_delete.html",
        {"evento": evento, "detalle": detalle},
    )


@administrador_required
def editar_servicio_evento(request, pk, detalle_pk):
    evento = get_object_or_404(Evento, pk=pk)
    detalle = get_object_or_404(DetalleEvento, pk=detalle_pk, evento=evento)

    if request.method == "POST":
        form = EditarDetalleEventoForm(
            request.POST,
            instance=detalle,
            evento=evento,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Servicio del evento actualizado correctamente.")
            return redirect("detalle_eventos", pk=evento.pk)
    else:
        form = EditarDetalleEventoForm(instance=detalle, evento=evento)

    return render(
        request,
        "eventos/servicios/servicio_form.html",
        {"evento": evento, "detalle": detalle, "form": form},
    )

@administrador_required
def agregar_implemento_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)

    if request.method != "POST":
        return redirect("detalle_eventos", pk=pk)
    
    form = UsoImplemtosForm(request.POST, evento=evento)

    if form.is_valid():
        implemento = form.cleaned_data["implemento"]

        if UsoImplemento.objects.filter(evento=evento,implemento=implemento,).exists():
            form.add_error("implemento", "Este implemento ya está agregado al evento.")
        else:
            uso = form.save(commit=False)
            uso.evento = evento
            uso.save()
            messages.success(request, "Implemento agregado al evento.")
            return redirect("detalle_eventos", pk=pk)
    return mostrar_detalle_evento(request,evento,form_implemento=form)


@administrador_required
def editar_uso_implemento(request, pk, uso_pk):
    evento = get_object_or_404(Evento, pk=pk)
    uso = get_object_or_404(UsoImplemento, pk=uso_pk, evento=evento)

    if request.method == "POST":
        form = EditarUsoImplementoForm(request.POST, instance=uso)
        if form.is_valid():
            form.save()
            messages.success(request, "Cantidad del implemento actualizada correctamente.")
            return redirect("detalle_eventos", pk=evento.pk)
    else:
        form = EditarUsoImplementoForm(instance=uso)

    return render(request,"eventos/implementos/uso_implemento_form.html",{"evento": evento, "uso": uso, "form": form})


@administrador_required
def eliminar_uso_implemento(request, pk, uso_pk):
    evento = get_object_or_404(Evento, pk=pk)
    uso = get_object_or_404(UsoImplemento, pk=uso_pk, evento=evento)

    if request.method == "POST":
        uso.delete()
        messages.success(request, "Implemento quitado del evento; su stock quedó disponible.")
        return redirect("detalle_eventos", pk=evento.pk)

    return render(request,"eventos/implementos/uso_implemento_delete.html",{"evento": evento, "uso": uso})

@administrador_required
def agregar_trabajador_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if request.method != "POST":
        return redirect("detalle_eventos", pk=pk)
    form = ParticipacionTrabajadorForm(request.POST)
    if form.is_valid():
        trabajador = form.cleaned_data["trabajador"]
        ya_asignado = ParticipacionTrabajador.objects.filter(evento=evento,trabajador=trabajador).exists()
        if ya_asignado:
            form.add_error("trabajador","Este trabajador ya está asignado a este evento.")
        else:
            participacion = form.save(commit=False)
            participacion.evento = evento
            participacion.save()
            messages.success(request, "Trabajador agregado al evento.")
            return redirect("detalle_eventos", pk=pk)
    return mostrar_detalle_evento(request,evento,form_trabajador=form)


@administrador_required
def editar_participacion_trabajador(request, pk, participacion_pk):
    evento = get_object_or_404(Evento, pk=pk)
    participacion = get_object_or_404(
        ParticipacionTrabajador,
        pk=participacion_pk,
        evento=evento,
    )

    if request.method == "POST":
        form = EditarParticipacionTrabajadorForm(
            request.POST,
            instance=participacion,
            evento=evento,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Participación del trabajador actualizada correctamente.")
            return redirect("detalle_eventos", pk=evento.pk)
    else:
        form = EditarParticipacionTrabajadorForm(
            instance=participacion,
            evento=evento,
        )

    return render(
        request,
        "eventos/trabajadores/participacion_trabajador_form.html",
        {"evento": evento, "participacion": participacion, "form": form},
    )


@administrador_required
def eliminar_participacion_trabajador(request, pk, participacion_pk):
    evento = get_object_or_404(Evento, pk=pk)
    participacion = get_object_or_404(
        ParticipacionTrabajador,
        pk=participacion_pk,
        evento=evento,
    )

    if request.method == "POST":
        participacion.delete()
        messages.success(request, "Trabajador quitado del evento.")
        return redirect("detalle_eventos", pk=evento.pk)

    return render(
        request,
        "eventos/trabajadores/participacion_trabajador_delete.html",
        {"evento": evento, "participacion": participacion},
    )

@administrador_required
def registrar_feedback_trabajador(request, evento_pk, participacion_pk):
    evento = get_object_or_404(Evento, pk=evento_pk)
    participacion = get_object_or_404(ParticipacionTrabajador,pk=participacion_pk,evento=evento)
    if FeedbackTrabajador.objects.filter(participacion=participacion).exists():
        messages.info(request, "Esta participación ya tiene un feedback.")
        return redirect("detalle_eventos", pk=evento.pk)
    if request.method == "POST":
        form = FeedbackTrabajadorForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.participacion = participacion
            feedback.evaluado_por = request.user
            feedback.save()
            messages.success(request, "Feedback registrado correctamente.")
            return redirect("detalle_eventos", pk=evento.pk)
    else:
        form = FeedbackTrabajadorForm()

    return render(request,"eventos/trabajadores/evento_feedback.html",{"evento": evento,"participacion": participacion,"form": form})
