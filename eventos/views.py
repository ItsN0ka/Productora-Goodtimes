from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import ProtectedError
from .models import Evento, Servicio, DetalleEvento, Implemento, UsoImplemento, ParticipacionTrabajador, FeedbackTrabajador
from django.contrib.auth.decorators import login_required
from .forms import EventoForm

# Create your views here.

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
    return render(request, "eventos/evento/evento_detail.html", {"evento": evento})

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
