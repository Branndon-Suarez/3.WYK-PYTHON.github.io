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

        user = self.model(num_doc=num_doc, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, num_doc, nombre, email_usuario, tel_usuario, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('estado_usuario', True)

        # Agregamos manualmente los campos que Django pide por consola
        extra_fields['nombre'] = nombre
        extra_fields['email_usuario'] = email_usuario
        extra_fields['tel_usuario'] = tel_usuario

        # LÓGICA DE PROTECCIÓN PARA EL ROL:
        try:
            rol_admin = Rol.objects.filter(clasificacion='ADMINISTRADOR').first()
            if not rol_admin:
                raise ValueError(
                    "No existe ningún ROL con clasificación 'ADMINISTRADOR' en la base de datos. Créalo primero en la shell.")
            extra_fields.setdefault('rol_fk_usuario', rol_admin)
        except Exception:
            raise ValueError(
                "Error al acceder a la tabla ROL. Asegúrate de tener la tabla creada y el rol ADMINISTRADOR registrado.")

        return self.create_user(num_doc, password, **extra_fields)


# ---------------------------------MODELO USUARIO---------------------------------
class Usuario(AbstractBaseUser, PermissionsMixin):
    id_usuario = models.AutoField(primary_key=True, db_column='id_usuario')
    num_doc = models.BigIntegerField(unique=True, db_column='num_doc')
    nombre = models.CharField(max_length=50, db_column='nombre')
    password = models.CharField(max_length=255, db_column='password_usuario')
    tel_usuario = models.BigIntegerField(db_column='tel_usuario')
    email_usuario = models.EmailField(max_length=50, unique=True, db_column='email_usuario')
    fecha_registro = models.DateTimeField(db_column='fecha_registro', auto_now_add=True)

    rol_fk_usuario = models.ForeignKey(
        Rol,
        on_delete=models.PROTECT,
        db_column='rol_fk_usuario'
    )

    # Mapeamos cada campo a su columna exacta del SQL
    # Usamos estado_usuario como el nombre principal para tu lógica de negocio
    estado_usuario = models.BooleanField(default=True, db_column='estado_usuario')

    # Django usará estos para los permisos y el login
    is_active = models.BooleanField(default=True, db_column='is_active')
    is_staff = models.BooleanField(default=False, db_column='is_staff')
    is_superuser = models.BooleanField(default=False, db_column='is_superuser')
    last_login = models.DateTimeField(null=True, blank=True, db_column='last_login')

    objects = UsuarioManager()

    USERNAME_FIELD = 'num_doc'
    REQUIRED_FIELDS = ['nombre', 'email_usuario', 'tel_usuario']

    # --- Metodo de sincronizacion estado inactivo ---
    def save(self, *args, **kwargs):
        # Si el usuario es desactivado administrativamente,
        # se le quita el permiso de acceso automáticamente.
        self.is_active = self.estado_usuario
        super().save(*args, **kwargs)

        # SOLUCIÓN AL ERROR DE ELIMINACIÓN:
    def delete(self, *args, **kwargs):
        """
        Limpia las relaciones virtuales de grupos y permisos para que Django
        no busque las tablas 'usuario_groups' que no existen en el SQL manual.
        """
        if self.id_usuario:
            self.groups.clear()
            self.user_permissions.clear()
        return super(Usuario, self).delete(*args, **kwargs)


    class Meta:
        managed = False
        db_table = 'usuario'

    def __str__(self):
        return f"{self.nombre} ({self.rol_fk_usuario.rol})"


