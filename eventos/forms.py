from django import forms
from .models import Evento

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