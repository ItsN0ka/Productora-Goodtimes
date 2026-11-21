from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    Evento,
    DetalleEvento,
    Implemento,
    UsoImplemento,
    ParticipacionTrabajador,
    FeedbackTrabajador,
    cantidad_disponible_para_evento,
)

class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = (
            "nombre",
            "tipo",
            "fecha",
            "hora",
            "lugar",
            "descripcion",
            "estado",
        )

        widgets = {
            "fecha": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "hora": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        hoy = timezone.localdate()
        if not self.instance.pk or self.instance.fecha >= hoy:
            self.fields["fecha"].widget.attrs["min"] = hoy.isoformat()

        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                clase = "form-select"
            else:
                clase = "form-control"

            field.widget.attrs["class"] = clase

class DetalleEventoForm(forms.ModelForm):
    class Meta:
        model = DetalleEvento
        fields = ("servicio", "precio_acordado")
        widgets = {
            "servicio": forms.Select(attrs={"class": "form-select"}),
            "precio_acordado": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": "0.01"}),
        }


class EditarDetalleEventoForm(forms.ModelForm):
    class Meta:
        model = DetalleEvento
        fields = ("servicio", "precio_acordado")
        widgets = {
            "servicio": forms.Select(attrs={"class": "form-select"}),
            "precio_acordado": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "step": "0.01"}
            ),
        }

    def __init__(self, *args, evento=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.evento = evento

    def clean(self):
        cleaned_data = super().clean()
        servicio = cleaned_data.get("servicio")

        if self.evento and servicio:
            repetido = DetalleEvento.objects.filter(
                evento=self.evento,
                servicio=servicio,
            ).exclude(pk=self.instance.pk)
            if repetido.exists():
                self.add_error("servicio", "Este servicio ya está agregado al evento.")

        return cleaned_data

class UsoImplemtosForm(forms.ModelForm):
    class Meta:
        model = UsoImplemento
        fields = ("implemento", "cantidad", "observaciones")
        widgets = {
            "implemento": forms.Select(attrs={"class": "form-select"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, evento=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.evento = evento
        implementos = Implemento.objects.filter(
            activo=True,
            cantidad_disponible__gt=0,
        ).order_by("nombre")

        if self.evento:
            disponibles = [
                implemento.pk
                for implemento in implementos
                if cantidad_disponible_para_evento(implemento, self.evento) > 0
            ]
            implementos = implementos.filter(pk__in=disponibles)

        self.fields["implemento"].queryset = implementos
        if not implementos.exists():
            self.fields["implemento"].empty_label = "No hay implementos disponibles"

    def clean(self):
        cleaned_data = super().clean()
        implemento = cleaned_data.get("implemento")
        cantidad = cleaned_data.get("cantidad")

        if self.evento and implemento and cantidad:
            disponible = cantidad_disponible_para_evento(implemento, self.evento)
            if cantidad > disponible:
                self.add_error(
                    "cantidad",
                    f"Para la fecha {self.evento.fecha}, solo quedan "
                    f"{disponible} unidad(es) de este implemento.",
                )

        return cleaned_data


class EditarUsoImplementoForm(forms.ModelForm):
    class Meta:
        model = UsoImplemento
        fields = ("cantidad", "observaciones")
        widgets = {
            "cantidad": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

class ParticipacionTrabajadorForm(forms.ModelForm):
    class Meta:
        model = ParticipacionTrabajador
        fields = ("trabajador", "tarea", "observaciones")
        widgets = {
            "trabajador": forms.Select(attrs={"class": "form-select"}),
            "tarea": forms.TextInput(attrs={"class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        Usuario = get_user_model()
        self.fields["trabajador"].queryset = Usuario.objects.filter(perfil__rol__nombre="Trabajador").order_by("username")


class EditarParticipacionTrabajadorForm(forms.ModelForm):
    class Meta:
        model = ParticipacionTrabajador
        fields = ("trabajador", "tarea", "observaciones")
        widgets = {
            "trabajador": forms.Select(attrs={"class": "form-select"}),
            "tarea": forms.TextInput(attrs={"class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, evento=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.evento = evento
        Usuario = get_user_model()
        self.fields["trabajador"].queryset = Usuario.objects.filter(
            perfil__rol__nombre="Trabajador"
        ).order_by("username")

    def clean(self):
        cleaned_data = super().clean()
        trabajador = cleaned_data.get("trabajador")

        if self.evento and trabajador:
            repetido = ParticipacionTrabajador.objects.filter(
                evento=self.evento,
                trabajador=trabajador,
            ).exclude(pk=self.instance.pk)
            if repetido.exists():
                self.add_error(
                    "trabajador",
                    "Este trabajador ya está asignado a este evento.",
                )

            if (
                self.instance.pk
                and trabajador.pk != self.instance.trabajador_id
                and FeedbackTrabajador.objects.filter(
                    participacion=self.instance
                ).exists()
            ):
                self.add_error(
                    "trabajador",
                    "No puedes cambiar al trabajador porque esta participación ya tiene feedback.",
                )

        return cleaned_data


class FeedbackTrabajadorForm(forms.ModelForm):
    class Meta:
        model = FeedbackTrabajador
        fields = ("calificacion", "comentario")
        widgets = {
            "calificacion": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 5}),
            "comentario": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
