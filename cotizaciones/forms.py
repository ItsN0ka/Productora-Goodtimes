from django import forms
from django.db import models
from eventos.models import (
    Evento,
    Servicio,
    Implemento,
    cantidad_disponible_para_evento,
)
from .models import (
    SolicitudCotizacion,
    Cotizacion,
    DetalleServicioCotizacion,
    DetalleImplementoCotizacion,
)

class SolicitudCotizacionForm(forms.ModelForm):
    class Meta:
        model = SolicitudCotizacion
        #lo que el cliente llena
        fields = ['nombre_evento',
                  'tipo_evento',
                  'fecha',
                  'hora',
                  'lugar',
                  'cantidad_asistencia',
                  'comentario']
        #calendario y reloj para fecha y hora
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'hora': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
        }

class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        #lo que llena el administrador, la solicitud y el estado los asigna el sistema
        # El precio se calcula sumando las líneas de servicio e implementos.
        fields = ['descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
        }


class DetalleServicioCotizacionForm(forms.ModelForm):
    class Meta:
        model = DetalleServicioCotizacion
        fields = ('servicio', 'precio_acordado')
        widgets = {
            'servicio': forms.Select(attrs={'class': 'form-select'}),
            'precio_acordado': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 0, 'step': '0.01'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        disponibles = Servicio.objects.filter(activo=True)
        if self.instance.pk and self.instance.servicio_id:
            disponibles = Servicio.objects.filter(
                models.Q(activo=True) | models.Q(pk=self.instance.servicio_id)
            )
        self.fields['servicio'].queryset = disponibles.order_by('nombre')


class DetalleImplementoCotizacionForm(forms.ModelForm):
    class Meta:
        model = DetalleImplementoCotizacion
        fields = ('implemento', 'cantidad')
        widgets = {
            'implemento': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, fecha_evento=None, **kwargs):
        super().__init__(*args, **kwargs)
        if fecha_evento is None and self.instance.pk:
            fecha_evento = self.instance.cotizacion.solicitud.fecha
        self.fecha_evento = fecha_evento

        disponibles = Implemento.objects.filter(activo=True)
        if self.instance.pk and self.instance.implemento_id:
            disponibles = Implemento.objects.filter(
                models.Q(activo=True) | models.Q(pk=self.instance.implemento_id)
            )
        self.fields['implemento'].queryset = disponibles.order_by('nombre')
        self.fields['cantidad'].help_text = (
            f'Stock calculado para el {self.fecha_evento:%d/%m/%Y}.'
            if self.fecha_evento else 'La cantidad se comprobará con el stock disponible.'
        )

    def clean(self):
        cleaned_data = super().clean()
        implemento = cleaned_data.get('implemento')
        cantidad = cleaned_data.get('cantidad')

        if implemento and cantidad and self.fecha_evento:
            evento_consulta = Evento(fecha=self.fecha_evento)
            disponible = cantidad_disponible_para_evento(implemento, evento_consulta)
            if cantidad > disponible:
                self.add_error(
                    'cantidad',
                    f'Para el {self.fecha_evento:%d/%m/%Y} solo hay '
                    f'{disponible} unidad(es) disponibles de {implemento.nombre}.',
                )
        return cleaned_data
