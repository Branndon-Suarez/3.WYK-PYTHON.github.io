from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


# ---------------------------------MODELO ROL---------------------------------
class Rol(models.Model):
    class Clasificacion(models.TextChoices):
        EMPLEADO = 'EMPLEADO', 'Empleado'
        ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'

    id_rol = models.AutoField(primary_key=True, db_column='id_rol')
    rol = models.CharField(max_length=50, db_column='rol')  # Ejemplo: 'ADMIN', 'MESERO', 'CAJERO'
    clasificacion = models.CharField(max_length=20, choices=Clasificacion.choices, db_column='clasificacion')
    estado_rol = models.BooleanField(db_column='estado_rol', default=True)

    class Meta:
        managed = False
        db_table = 'rol'

    def __str__(self):
        return f"{self.rol} [{self.clasificacion}]"


# ---------------------------------MANAGER PARA USUARIO---------------------------------
class UsuarioManager(BaseUserManager):
    def create_user(self, num_doc, password=None, **extra_fields):
        if not num_doc:
            raise ValueError('El número de documento es obligatorio')

        # Aquí forzamos que si no viene un rol, el sistema lance error (excepto en el shell si lo manejamos)
        user = self.model(num_doc=num_doc, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, num_doc, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        # LÓGICA DE PROTECCIÓN:
        # Intentamos buscar el primer rol que sea de clasificación ADMINISTRADOR
        try:
            rol_admin = Rol.objects.filter(clasificacion='ADMINISTRADOR').first()
            if not rol_admin:
                raise ValueError(
                    "No existe ningún ROL con clasificación 'ADMINISTRADOR' en la base de datos. Créalo primero en Postgres.")
            extra_fields.setdefault('rol_fk_usuario', rol_admin)
        except Exception:
            raise ValueError(
                "Error al acceder a la tabla ROL. Asegúrate de haber corrido las migraciones y tener roles creados.")

        return self.create_user(num_doc, password, **extra_fields)


# ---------------------------------MODELO USUARIO---------------------------------
class Usuario(AbstractBaseUser, PermissionsMixin):
    id_usuario = models.AutoField(primary_key=True, db_column='id_usuario')
    num_doc = models.BigIntegerField(unique=True, db_column='num_doc')
    nombre = models.CharField(max_length=50, db_column='nombre')
    password = models.CharField(max_length=150, db_column='password_usuario')
    tel_usuario = models.BigIntegerField(db_column='tel_usuario')
    email_usuario = models.EmailField(max_length=50, unique=True, db_column='email_usuario')
    fecha_registro = models.DateTimeField(db_column='fecha_registro', auto_now_add=True)

    # CAMPO ESTRICTO: Sin null=True. Obliga a tener un Rol.
    rol_fk_usuario = models.ForeignKey(
        Rol,
        on_delete=models.PROTECT,
        db_column='rol_fk_usuario'
    )

    estado_usuario = models.BooleanField(default=True, db_column='estado_usuario')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'num_doc'
    REQUIRED_FIELDS = ['nombre', 'email_usuario']

    class Meta:
        managed = False
        db_table = 'usuario'

    def __str__(self):
        return f"{self.nombre} ({self.rol_fk_usuario.rol})"


# ---------------------------------MODELO TAREA---------------------------------

class Tarea(models.Model):
    class Prioridad(models.TextChoices):
        BAJA = 'BAJA', 'Baja'
        MEDIA = 'MEDIA', 'Media'
        ALTA = 'ALTA', 'Alta'

    class EstadoTarea(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        COMPLETADA = 'COMPLETADA', 'Completada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    id_tarea = models.AutoField(primary_key=True, db_column='id_tarea')
    tarea = models.CharField(max_length=100, db_column='tarea')
    categoria = models.CharField(max_length=80, db_column='categoria')
    descripcion = models.CharField(max_length=250, blank=True, null=True, db_column='descripcion')
    tiempo_estimado_horas = models.FloatField(db_column='tiempo_estimado_horas')

    prioridad = models.CharField(max_length=10, choices=Prioridad.choices, db_column='prioridad')

    # AJUSTAR ESTA LÍNEA:
    estado_tarea = models.CharField(
        max_length=15,
        choices=EstadoTarea.choices,  # <--- Agregamos los choices
        db_column='estado_tarea'  # Verifica si en tu SQL es ESTADO_TAREA o ESTADO_REA
    )

    usuario_asignado_fk = models.ForeignKey(Usuario, on_delete=models.PROTECT, db_column='usuario_asignado_fk',
                                            related_name='tareas_asignadas')
    usuario_creador_fk = models.ForeignKey(Usuario, on_delete=models.PROTECT, db_column='usuario_creador_fk',
                                           related_name='tareas_creadas')

    class Meta:
        managed = False
        db_table = 'tarea'