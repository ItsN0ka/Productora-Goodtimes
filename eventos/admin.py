from django.contrib import admin
from .models import Evento, Servicio, DetalleEvento, Implemento, UsoImplemento, ParticipacionTrabajador, FeedbackTrabajador

# Register your models here.

admin.site.register(Evento)
admin.site.register(Servicio)
admin.site.register(DetalleEvento)
admin.site.register(Implemento)
admin.site.register(UsoImplemento)
admin.site.register(ParticipacionTrabajador)
admin.site.register(FeedbackTrabajador)