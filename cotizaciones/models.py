from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

class SolicitudCotizacion(models.Model):
    ESTADOS = [
        ('PEN', 'Pendiente'),
        ('INF', 'Información solicitada'),
        ('ACE', 'Aceptada'),
        ('REC', 'Rechazada'),
    ]
    MAGNITUDES = [
        ('PEQ', 'Pequeño'),
        ('MED', 'Mediano'),
        ('GRA', 'Grande'),
    ]
    #tiempo que quedara bloqueado dependiendo la magnitud, si es pequeño o mediano
    HORAS_BLOQUEO = {'PEQ': 4, 'MED': 8}
    #relacion uno a muchos un cliente puede solicitar muchas solicitudes 
    #PROTECT no permite eliminar el usuario si tiene solicitudes asociadas
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='solicitudes', verbose_name='Cliente')
    tipo_evento = models.CharField(max_length=45, verbose_name='Tipo de evento')
    nombre_evento = models.CharField(max_length=45, verbose_name='Nombre del evento')
    cantidad_asistencia = models.PositiveIntegerField(verbose_name='Cantidad de asistentes')
    lugar = models.CharField(max_length=45, verbose_name='Lugar')
    fecha = models.DateField(verbose_name='Fecha')
    hora = models.TimeField(verbose_name='Hora')
    #la magnitud define cuantas horas del dia ocupa el evento
    magnitud = models.CharField(max_length=3, choices=MAGNITUDES, default='PEQ', verbose_name='Magnitud')
    comentario = models.TextField(verbose_name='Comentario', blank=True)
    #por defecto la solicitud queda pendiente
    estado = models.CharField(max_length=3, choices=ESTADOS, default='PEN', verbose_name='Estado')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de solicitud')
    evento = models.OneToOneField(
        'eventos.Evento', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='solicitud_origen', verbose_name='Evento creado al aceptar',
    )

    class Meta:
        verbose_name = 'Solicitud de cotización'
        verbose_name_plural = 'Solicitudes de cotización'

    def __str__(self):
        return f'Solicitud #{self.id} - {self.nombre_evento}'


class Cotizacion(models.Model):
    ESTADOS = [
        ('BOR', 'Borrador'),
        ('ENV', 'Enviada'),
        ('ACE', 'Aceptada'),
        ('REC', 'Rechazada'),
    ]
    #relacion uno a uno cada solicitud tiene una sola cotizacion
    #CASCADE si se elimina la solicitud se elimina su cotizacion
    solicitud = models.OneToOneField(SolicitudCotizacion, on_delete=models.CASCADE, related_name='cotizacion', verbose_name='Solicitud')
    #relacion uno a muchos un administrador puede preparar muchas cotizaciones
    administrador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='cotizaciones', verbose_name='Administrador')
    descripcion = models.TextField(blank=True, verbose_name='Descripción de la propuesta')
    precio = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0'))], verbose_name='Precio total',
    )
    #por defecto la cotizacion queda enviada al cliente
    estado = models.CharField(max_length=3, choices=ESTADOS, default='BOR', verbose_name='Estado')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de cotización')

    class Meta:
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'

    def __str__(self):
        return f'Cotización #{self.id} - {self.solicitud.nombre_evento}'

    def calcular_total(self):
        total_servicios = sum(
            (linea.precio_acordado for linea in self.detalles_servicios.all()),
            Decimal('0.00'),
        )
        return total_servicios


class DetalleServicioCotizacion(models.Model):
    cotizacion = models.ForeignKey(
        Cotizacion, on_delete=models.CASCADE, related_name='detalles_servicios'
    )
    servicio = models.ForeignKey(
        'eventos.Servicio', on_delete=models.PROTECT, related_name='detalles_cotizaciones'
    )
    precio_acordado = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Precio acordado',
    )

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['cotizacion', 'servicio'], name='servicio_unico_por_cotizacion'
        )]
        verbose_name = 'Servicio cotizado'
        verbose_name_plural = 'Servicios cotizados'

    def __str__(self):
        return f'{self.servicio} - cotización #{self.cotizacion_id}'


class DetalleImplementoCotizacion(models.Model):
    cotizacion = models.ForeignKey(
        Cotizacion, on_delete=models.CASCADE, related_name='detalles_implementos'
    )
    implemento = models.ForeignKey(
        'eventos.Implemento', on_delete=models.PROTECT, related_name='detalles_cotizaciones'
    )
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['cotizacion', 'implemento'], name='implemento_unico_por_cotizacion'
        )]
        verbose_name = 'Implemento cotizado'
        verbose_name_plural = 'Implementos cotizados'

    def __str__(self):
        return f'{self.cantidad} x {self.implemento} - cotización #{self.cotizacion_id}'
