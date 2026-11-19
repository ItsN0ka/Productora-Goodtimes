from django.urls import path
from . import views

urlpatterns = [
    path("", views.lista_eventos, name="lista_eventos"),
    path("crear/",views.crear_evento, name="crear_eventos"),
    path("<int:pk>/", views.detalle_evento, name="detalle_eventos"),
    path("<int:pk>/editar/", views.editar_evento, name="editar_evento"),
    path("<int:pk>/eliminar/", views.eliminar_evento, name="eliminar_eventos"),
]