from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import ProtectedError
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from .forms import LoginForm
from .models import Rol, Usuario  # Importamos Usuario aquí para evitar el try-import dentro de la función


# ------------------------------ AUTENTICACIÓN ------------------------------

def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('inicio')
        else:
            num_doc = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, num_doc=num_doc, password=password)

            try:
                usuario_db = Usuario.objects.get(num_doc=num_doc)
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
    return render(request, 'usuarios/inicio.html')


# ------------------------------ FUNCIONES DE ROLES (CRUD) ------------------------------

@login_required
def lista_roles(request):
    """Dashboard de Roles: lista.html"""
    roles = Rol.objects.all().order_by('id_rol')
    return render(request, 'usuarios/rol/lista.html', {'roles': roles})


@login_required
def crear_rol(request):
    """Formulario de Creación: crear.html"""
    if request.method == 'POST':
        rol_nombre = request.POST.get('rol').upper()
        clasificacion = request.POST.get('clasificacion')

        if rol_nombre and clasificacion:
            Rol.objects.create(
                rol=rol_nombre,
                clasificacion=clasificacion,
                estado_rol=True
            )
            messages.success(request, f"Rol '{rol_nombre}' creado correctamente.")
            return redirect('lista_roles')

    clasificaciones = Rol.Clasificacion.choices
    return render(request, 'usuarios/rol/crear.html', {'clasificaciones': clasificaciones})


@login_required
def editar_rol(request, id_rol):
    """Formulario de Actualización: editar.html"""
    rol = get_object_or_404(Rol, id_rol=id_rol)

    if request.method == 'POST':
        rol.rol = request.POST.get('rol').upper()
        rol.clasificacion = request.POST.get('clasificacion')
        # Captura el estado del checkbox
        rol.estado_rol = 'estado_rol' in request.POST
        rol.save()
        messages.success(request, f"Rol '{rol.rol}' actualizado correctamente.")
        return redirect('lista_roles')

    clasificaciones = Rol.Clasificacion.choices
    return render(request, 'usuarios/rol/editar.html', {
        'rol': rol,
        'clasificaciones': clasificaciones
    })


@login_required
def eliminar_rol(request, id_rol):
    """Acción de eliminación con protección de base de datos"""
    rol = get_object_or_404(Rol, id_rol=id_rol)

    # Nota: El SweetAlert en lista.html envía un POST
    if request.method == 'POST':
        try:
            rol.delete()
            messages.success(request, "Rol eliminado correctamente.")
        except ProtectedError:
            messages.error(request, f"No se puede eliminar '{rol.rol}' porque tiene usuarios vinculados.")

    return redirect('lista_roles')