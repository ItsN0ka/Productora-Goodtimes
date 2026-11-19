from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import ProtectedError
from .models import Evento, Servicio, DetalleEvento, Implemento, UsoImplemento, ParticipacionTrabajador, FeedbackTrabajador
from django.contrib.auth.decorators import login_required
from .forms import EventoForm, DetalleEventoForm, UsoImplemtosForm

# Create your views here.
#Evento
def lista_eventos(request):
    eventos = Evento.objects.order_by("fecha")
    return render(request, "eventos/evento/evento_list.html", {"eventos": eventos})

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

def detalle_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    return mostrar_detalle_evento(request, evento)

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

def mostrar_detalle_evento(request, evento, form_servicio=None, form_implemento=None):
    contexto = {
        "evento": evento,
        "servicios_evento": evento.servicios.select_related("servicio"),
        "implementos_evento": evento.implementos_usados.select_related("implemento"),
        "form_servicio": (form_servicio if form_servicio is not None else DetalleEventoForm()),
        "form_implemento": ( form_implemento if form_implemento is not None else UsoImplemtosForm()),
    }
    return render(request, "eventos/evento/evento_detail.html", contexto)

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

def agregar_implemento_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)

    if request.method != "POST":
        return redirect("detalle_eventos", pk=pk)
    
    form = UsoImplemtosForm(request.POST)

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