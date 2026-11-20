from django.db import models
from django.conf import settings

class SolicitudCotizacion(models.Model):
    ESTADOS = [
        ('PEN', 'Pendiente'),
        ('INF', 'Información solicitada'),
        ('ACE', 'Aceptada'),
        ('REC', 'Rechazada'),
    ]
    #relacion uno a muchos un cliente puede solicitar muchas solicitudes 
    #PROTECT no permite eliminar el usuario si tiene solicitudes asociadas
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='solicitudes', verbose_name='Cliente')
    #relacion uno a muchos un administrador puede revisar muchas solicitudes
    #queda vacio hasta que un administrador la revise
    administrador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='solicitudes_revisadas', verbose_name='Administrador', null=True, blank=True)
    tipo_evento = models.CharField(max_length=45, verbose_name='Tipo de evento')
    nombre_evento = models.CharField(max_length=45, verbose_name='Nombre del evento')
    cantidad_asistencia = models.PositiveIntegerField(verbose_name='Cantidad de asistentes')
    lugar = models.CharField(max_length=45, verbose_name='Lugar')
    fecha = models.DateField(verbose_name='Fecha')
    hora = models.TimeField(verbose_name='Hora')
    comentario = models.TextField(verbose_name='Comentario', blank=True)
    #por defecto la solicitud queda pendiente
    estado = models.CharField(max_length=3, choices=ESTADOS, default='PEN', verbose_name='Estado')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de solicitud')

    class Meta:
        verbose_name = 'Solicitud de cotización'
        verbose_name_plural = 'Solicitudes de cotización'

    def __str__(self):
        return f'Solicitud #{self.id} - {self.nombre_evento}'