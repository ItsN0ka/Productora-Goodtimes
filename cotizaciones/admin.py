from django.contrib import admin
from .models import (
    SolicitudCotizacion,
    Cotizacion,
    DetalleServicioCotizacion,
    DetalleImplementoCotizacion,
)

admin.site.register(SolicitudCotizacion)
admin.site.register(Cotizacion)
admin.site.register(DetalleServicioCotizacion)
admin.site.register(DetalleImplementoCotizacion)
