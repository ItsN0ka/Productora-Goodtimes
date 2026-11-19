from django.urls import path
from . import views

urlpatterns = [
    #Eventos
    path("", views.lista_eventos, name="lista_eventos"),
    path("crear/",views.crear_evento, name="crear_eventos"),
    path("<int:pk>/", views.detalle_evento, name="detalle_eventos"),
    path("<int:pk>/editar/", views.editar_evento, name="editar_evento"),
    path("<int:pk>/eliminar/", views.eliminar_evento, name="eliminar_eventos"),
    #Detalle_eventos
    path("<int:pk>/agregar-servicio/",views.agregar_servicio_evento, name="agregar_servicio_evento",),
    path("<int:pk>/agregar-implemento/",views.agregar_implemento_evento, name="agregar_implemento_evento",),
]