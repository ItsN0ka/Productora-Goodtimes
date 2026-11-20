from django import forms
from .models import SolicitudCotizacion

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