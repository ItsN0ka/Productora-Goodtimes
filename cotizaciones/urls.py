from django.urls import path
from . import views

urlpatterns = [
    #cotizaciones del cliente
    path('', views.mis_cotizaciones, name='mis_cotizaciones'),
    path('crear/', views.crear_cotizacion, name='crear_cotizacion'),
    path('<int:pk>/', views.detalle_cotizacion, name='detalle_cotizacion'),

    #panel del administrador
    path('solicitudes/', views.lista_solicitudes, name='lista_solicitudes'),
    path('solicitudes/<int:pk>/cotizar/', views.preparar_cotizacion, name='preparar_cotizacion'),
]
