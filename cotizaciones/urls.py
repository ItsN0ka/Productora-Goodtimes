from django.urls import path
from . import views

urlpatterns = [
    #cliente
    path('', views.mis_cotizaciones, name='mis_cotizaciones'),
    path('crear/', views.crear_cotizacion, name='crear_cotizacion'),
    path('<int:pk>/', views.detalle_cotizacion, name='detalle_cotizacion'),
    path('<int:pk>/responder/',views.responder_solicitud, name='responder_solicitud'),
    path('<int:pk>/aceptar/', views.aceptar_cotizacion, name='aceptar_cotizacion'),
    path('<int:pk>/rechazar/', views.rechazar_cotizacion, name='rechazar_cotizacion'),
    path('<int:pk>/servicios/agregar/', views.agregar_servicio_cotizacion, name='agregar_servicio_cotizacion'),
    path('<int:pk>/implementos/agregar/', views.agregar_implemento_cotizacion, name='agregar_implemento_cotizacion'),
    path('<int:pk>/<str:tipo>/<int:detalle_pk>/editar/', views.editar_detalle_cotizacion, name='editar_detalle_cotizacion'),
    path('<int:pk>/<str:tipo>/<int:detalle_pk>/eliminar/', views.eliminar_detalle_cotizacion, name='eliminar_detalle_cotizacion'),
    path('<int:pk>/enviar/', views.enviar_cotizacion, name='enviar_cotizacion'),
    #admin
    path('solicitudes/', views.lista_solicitudes, name='lista_solicitudes'),
]
