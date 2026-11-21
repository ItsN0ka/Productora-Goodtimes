from django.db import models
from django.db.models import Sum
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone

class Evento(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        CONFIRMADO = "confirmado", "Confirmado"
        REALIZADO = "realizado", "Realizado"
        CANCELADO = "cancelado", "Cancelado"

    nombre = models.CharField(max_length=120)
    tipo = models.CharField(max_length=80)
    fecha = models.DateField()
    hora = models.TimeField(null=True, blank=True)
    lugar = models.CharField(max_length=180)
    descripcion = models.TextField(blank=True)
    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    cantidad_asistencia = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1)],
                                                      verbose_name="Cantidad de asistentes")

    def __str__(self):
        return f"{self.nombre} - {self.fecha}"

    def clean(self):
        super().clean()

        if self.fecha and self.fecha < timezone.localdate():
            fecha_original = None
            if self.pk:
                fecha_original = type(self).objects.filter(pk=self.pk).values_list(
                    "fecha", flat=True
                ).first()

            # Permite conservar y editar eventos, pero no crear ni
            # cambiar un evento para que tenga una fecha pasada.
            if fecha_original != self.fecha:
                raise ValidationError({
                    "fecha": "La fecha del evento debe ser hoy o una fecha futura."
                })

        if not self.pk or self.estado == self.Estado.CANCELADO:
            return

        for uso in self.implementos_usados.select_related("implemento"):
            disponible = cantidad_disponible_para_evento(
                uso.implemento,
                self,
                excluir_evento_id=self.pk,
            )
            if uso.cantidad > disponible:
                raise ValidationError({
                    "fecha": (
                        f"No se puede asignar esta fecha: quedan {disponible} "
                        f"unidad(es) de {uso.implemento.nombre}, pero este evento "
                        f"tiene asignadas {uso.cantidad}."
                    )
                })

class Servicio(models.Model):
    nombre = models.CharField(max_length=180, unique=True)
    descripcion = models.TextField(blank=True)
    precio_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class DetalleEvento(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="servicios")
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT, related_name="eventos")
    precio_acordado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "servicio"],
                name="servicio_unico_por_evento",
            )
        ]

    def __str__(self):
        return f"{self.servicio} - {self.evento}"

class Implemento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    cantidad_disponible = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class UsoImplemento(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="implementos_usados")
    implemento = models.ForeignKey(Implemento, on_delete=models.PROTECT, related_name="usos")
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    observaciones = models.TextField(blank=True)

    def clean(self):
        super().clean()
        if self.evento_id and self.implemento_id and self.cantidad is not None:
            disponible = cantidad_disponible_para_evento(
                self.implemento,
                self.evento,
                excluir_uso_id=self.pk,
            )
            if self.cantidad > disponible:
                raise ValidationError({
                    "cantidad": (
                        f"Para la fecha {self.evento.fecha}, solo quedan "
                        f"{disponible} unidad(es) de este implemento."
                    )
                })

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "implemento"],
                name="implemento_unico_por_evento",
            )
        ]

    def __str__(self):
        return f"{self.implemento} usado en {self.evento}"


def cantidad_disponible_para_evento(
    implemento,
    evento,
    excluir_uso_id=None,
    excluir_evento_id=None,
):
    
    reservas = UsoImplemento.objects.filter(
        implemento=implemento,
        evento__fecha=evento.fecha,
    ).exclude(evento__estado=Evento.Estado.CANCELADO)

    if excluir_uso_id:
        reservas = reservas.exclude(pk=excluir_uso_id)
    if excluir_evento_id:
        reservas = reservas.exclude(evento_id=excluir_evento_id)

    cantidad_reservada = reservas.aggregate(total=Sum("cantidad"))["total"] or 0
    return max(0, implemento.cantidad_disponible - cantidad_reservada)

class ParticipacionTrabajador(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="participaciones")
    trabajador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="participaciones_eventos")
    tarea = models.CharField(max_length=150)
    observaciones = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "trabajador"],
                name="participacion_unica_por_trabajador_y_evento",
            )
        ]

    def __str__(self):
        return f"{self.trabajador} - {self.evento}"

class FeedbackTrabajador(models.Model):
    participacion = models.OneToOneField(ParticipacionTrabajador, on_delete=models.CASCADE, related_name="feedback")
    evaluado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="feedback_realizados")
    calificacion = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback de {self.participacion.trabajador}"
