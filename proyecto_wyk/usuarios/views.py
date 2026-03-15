from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import ProtectedError
# --- NUEVAS IMPORTACIONES PARA EL LOGIN ---
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from .forms import LoginForm
from .models import Rol


# ------------------------------ AUTENTICACIÓN ------------------------------

def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            # Si llegamos aquí, los datos existen y el usuario está activo
            user = form.get_user()
            auth_login(request, user)
            return redirect('inicio')
        else:
            # Si el formulario NO es válido, investigamos por qué:
            num_doc = request.POST.get('username')  # 'username' es el nombre del campo en AuthenticationForm
            password = request.POST.get('password')

            # Buscamos al usuario manualmente para ver si es que está inactivo
            user = authenticate(request, num_doc=num_doc, password=password)

            # Si authenticate es None pero el usuario existe, es porque está INACTIVO
            from .models import Usuario
            try:
                usuario_db = Usuario.objects.get(num_doc=num_doc)
                # Si la contraseña es correcta pero no autenticó, revisamos is_active
                if usuario_db.check_password(password) and not usuario_db.is_active:
                    messages.error(request,
                                   "Acceso denegado. Tu cuenta está inactiva, comunícate con el administrador.")
                else:
                    messages.error(request, "Número de documento o contraseña incorrectos.")
            except Usuario.DoesNotExist:
                messages.error(request, "Número de documento o contraseña incorrectos.")
    else:
        form = LoginForm()

    return render(request, 'registration/login.html', {'form': form})




def logout_view(request):
    auth_logout(request)
    return redirect('login')


# ------------------------------ INICIO ------------------------------
@login_required
def inicio(request):
    # Django buscará este archivo en la carpeta global templates/inicio.html
    return render(request, 'usuarios/inicio.html')

# ------------------------------ FUNCIONES DE ROLES ------------------------------

# LISTAR ROLES
@login_required
def lista_roles(request):
    """Muestra todos los roles registrados en la tabla 'rol'"""
    roles = Rol.objects.all()
    return render(request, 'usuarios/rol/lista.html', {'roles': roles})


# CREAR ROL
@login_required
def crear_rol(request):
    """Inserta un nuevo registro en la tabla 'rol' validando los ENUM de Postgres"""
    if request.method == 'POST':
        rol_nombre = request.POST.get('rol').upper()  # Guardamos en mayúsculas por orden
        clasificacion = request.POST.get('clasificacion')

        # El campo estado_rol es BOOLEAN NOT NULL en tu DB
        if rol_nombre and clasificacion:
            Rol.objects.create(
                rol=rol_nombre,
                clasificacion=clasificacion,
                estado_rol=True  # Por defecto activo al crear
            )
            messages.success(request, f"Rol '{rol_nombre}' creado correctamente.")
            return redirect('lista_roles')

    # Pasamos las opciones del TextChoices definido en tu models.py
    clasificaciones = Rol.Clasificacion.choices
    return render(request, 'usuarios/rol/formulario.html', {'clasificaciones': clasificaciones})


# EDITAR ROL
@login_required
def editar_rol(request, id_rol):
    """Actualiza un rol existente buscando por su PK 'id_rol'"""
    rol = get_object_or_404(Rol, id_rol=id_rol)

    if request.method == 'POST':
        rol.rol = request.POST.get('rol').upper()
        rol.clasificacion = request.POST.get('clasificacion')
        # Manejo del checkbox para el campo BOOLEAN
        rol.estado_rol = 'estado_rol' in request.POST
        rol.save()
        messages.success(request, f"Rol '{rol.rol}' actualizado correctamente.")
        return redirect('lista_roles')

    clasificaciones = Rol.Clasificacion.choices
    return render(request, 'usuarios/rol/formulario.html', {
        'rol': rol,
        'clasificaciones': clasificaciones
    })


# ELIMINAR ROL
@login_required
def eliminar_rol(request, id_rol):
    """Borra un rol siempre que no tenga usuarios asociados (PROTECT)"""
    rol = get_object_or_404(Rol, id_rol=id_rol)

    if request.method == 'POST':
        try:
            rol.delete()
            messages.success(request, "Rol eliminado correctamente.")
            return redirect('lista_roles')
        except ProtectedError:
            # Captura el error si hay usuarios vinculados por FK en la DB
            messages.error(request, f"No se puede eliminar '{rol.rol}' porque existen usuarios con este rol.")
            return redirect('lista_roles')

    return render(request, 'usuarios/rol/eliminar.html', {'rol': rol})