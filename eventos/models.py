from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator

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

    def __str__(self):
        return f"{self.nombre} - {self.fecha}"

class Servicio(models.Model):
    nombre = models.CharField(max_length=180, unique=True)
    descripcion = models.TextField(blank=True)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class DetalleEvento(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="servicios")
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT, related_name="eventos")
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_acordado = models.DecimalField(max_digits=10, decimal_places=2)

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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "implemento"],
                name="implemento_unico_por_evento",
            )
        ]

    def __str__(self):
        return f"{self.implemento} usado en {self.evento}"

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