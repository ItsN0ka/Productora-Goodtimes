from django import forms
from .models import Evento, DetalleEvento, UsoImplemento

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

        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                clase = "form-select"
            else:
                clase = "form-control"

            field.widget.attrs["class"] = clase

class DetalleEventoForm(forms.ModelForm):
    class Meta:
        model = DetalleEvento
        fields = ("servicio", "cantidad", "precio_acordado")
        widgets = {
            "servicio": forms.Select(attrs={"class": "form-select"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "precio_acordado": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": "0.01"}),
        }

class UsoImplemtosForm(forms.ModelForm):
    class Meta:
        model = UsoImplemento
        fields = ("implemento", "cantidad", "observaciones")
        widgets = {
            "implemento": forms.Select(attrs={"class": "form-select"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }