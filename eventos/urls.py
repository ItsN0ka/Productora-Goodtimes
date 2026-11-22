from django.urls import path
from . import views

urlpatterns = [
    #Eventos
    path("", views.lista_eventos, name="lista_eventos"),
    path("crear/",views.crear_evento, name="crear_eventos"),
    path("resumenes/", views.lista_resumenes_eventos, name="lista_resumenes_eventos"),
    path("<int:pk>/", views.detalle_evento, name="detalle_eventos"),
    path("<int:pk>/resumen/", views.resumen_evento, name="resumen_evento"),
    path("<int:pk>/editar/", views.editar_evento, name="editar_evento"),
    path("<int:pk>/eliminar/", views.eliminar_evento, name="eliminar_eventos"),
    #Detalle_eventos
    path("<int:pk>/agregar-servicio/",views.agregar_servicio_evento, name="agregar_servicio_evento",),
    path("<int:pk>/servicios/<int:detalle_pk>/eliminar/", views.eliminar_servicio_evento, name="eliminar_servicio_evento"),
    path("<int:pk>/servicios/<int:detalle_pk>/editar/", views.editar_servicio_evento, name="editar_servicio_evento"),
    path("<int:pk>/agregar-implemento/",views.agregar_implemento_evento, name="agregar_implemento_evento",),
    path("<int:pk>/implementos/<int:uso_pk>/editar/", views.editar_uso_implemento, name="editar_uso_implemento"),
    path("<int:pk>/implementos/<int:uso_pk>/eliminar/", views.eliminar_uso_implemento, name="eliminar_uso_implemento"),
    #trabajador
    path("<int:pk>/agregar-trabajador/",views.agregar_trabajador_evento,name="agregar_trabajador_evento"),
    path("<int:pk>/participaciones/<int:participacion_pk>/editar/", views.editar_participacion_trabajador, name="editar_participacion_trabajador"),
    path("<int:pk>/participaciones/<int:participacion_pk>/eliminar/", views.eliminar_participacion_trabajador, name="eliminar_participacion_trabajador"),
    path("<int:evento_pk>/participaciones/<int:participacion_pk>/feedback/",views.registrar_feedback_trabajador,name="registrar_feedback_trabajador"),
]
