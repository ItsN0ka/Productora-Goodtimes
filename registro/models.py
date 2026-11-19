from django.db import models
<<<<<<< HEAD

# Create your models here.
=======
from django.contrib.auth.models import User

def rol_usuario_default():
    rol, _ =Rol.objects.get_or_create(nombre = 'Usuario')
    return rol.id

class Rol(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.nombre
    
class Perfil(models.Model):
    rol = models.ForeignKey(Rol, on_delete=models.RESTRICT, default= rol_usuario_default)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.user.username} - {self.rol.nombre}"
>>>>>>> origin/develop
