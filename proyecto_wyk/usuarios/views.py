from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import ProtectedError
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from .forms import LoginForm
from django.http import JsonResponse
import json
from .models import Rol, Usuario

# ------------------------------ AUTENTICACIÓN ------------------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    if request.method == 'POST':
        num_doc_post = request.POST.get('username')
        password_post = request.POST.get('password')

        # 1. VALIDACIÓN DE INACTIVOS (ALERTA ROJA)
        if num_doc_post:
            usuario_db = Usuario.objects.filter(num_doc=num_doc_post).first()
            if usuario_db:
                if not usuario_db.is_active:
                    messages.error(request, "Acceso denegado. Tu cuenta está inactiva. Contacta al administrador.")
                    return render(request, 'registration/login.html', {'form': LoginForm(request.POST)})

                if usuario_db.rol_fk_usuario and not usuario_db.rol_fk_usuario.estado_rol:
                    messages.error(request, f"Acceso denegado. El rol '{usuario_db.rol_fk_usuario.rol}' está inactivo. Contacta al administrador.")
                    return render(request, 'registration/login.html', {'form': LoginForm(request.POST)})

        # 2. INTENTO DE AUTENTICACIÓN (Independiente de form.is_valid)
        user = authenticate(request, num_doc=num_doc_post, password=password_post)

        if user is not None:
            auth_login(request, user)
            return redirect('inicio')
        else:
            # SI NO HAY USUARIO, ES EL TOAST NARANJA
            messages.error(request, "Número de documento o contraseña incorrectos.")
            return render(request, 'registration/login.html', {'form': LoginForm(request.POST)})

    else:
        form = LoginForm()

    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    return redirect('login')

# ------------------------------ SEGURIDAD AJAX ------------------------------

@login_required
def verificar_password_ajax(request):
    """ Verifica la contraseña mediante AJAX para preConfirm de SweetAlert2 """
    if request.method == 'POST':
        password = request.POST.get('password')
        is_valid = request.user.check_password(password)
        return JsonResponse({'valid': is_valid})

    return JsonResponse({'valid': False}, status=400)


# ------------------------------ INICIO ------------------------------
@login_required
def inicio(request):
    return render(request, 'usuarios/inicio.html')


# ------------------------------ FUNCIONES DE ROLES (CRUD) ------------------------------

@login_required
def lista_roles(request):
    roles = Rol.objects.all().order_by('id_rol')
    return render(request, 'usuarios/rol/lista.html', {'roles': roles})


@login_required
def crear_rol(request):
    clasificaciones = Rol.Clasificacion.choices

    if request.method == 'POST':
        rol_nombre = request.POST.get('rol', '').strip().upper()
        clasificacion = request.POST.get('clasificacion')

        if rol_nombre and clasificacion:
            if Rol.objects.filter(rol=rol_nombre).exists():
                messages.error(request, f"El nombre de rol '{rol_nombre}' ya está registrado.")
                return render(request, 'usuarios/rol/crear.html', {
                    'clasificaciones': clasificaciones,
                    'rol_digitado': rol_nombre
                })
            else:
                Rol.objects.create(rol=rol_nombre, clasificacion=clasificacion, estado_rol=True)
                messages.success(request, f"Rol '{rol_nombre}' creado correctamente.")
                return redirect('lista_roles')
        else:
            messages.error(request, "Todos los campos son obligatorios.")

    return render(request, 'usuarios/rol/crear.html', {'clasificaciones': clasificaciones})


@login_required
def editar_rol(request, id_rol):
    rol = get_object_or_404(Rol, id_rol=id_rol)
    clasificaciones = Rol.Clasificacion.choices

    if request.method == 'POST':
        nuevo_nombre = request.POST.get('rol', '').strip().upper()
        nueva_clasificacion = request.POST.get('clasificacion')

        if nuevo_nombre != rol.rol and Rol.objects.filter(rol=nuevo_nombre).exists():
            messages.error(request, f"Ya existe otro rol con el nombre '{nuevo_nombre}'.")
            return render(request, 'usuarios/rol/editar.html', {
                'rol': rol,
                'clasificaciones': clasificaciones,
                'nombre_intentado': nuevo_nombre,
                'clasificacion_intentada': nueva_clasificacion,
            })
        else:
            rol.rol = nuevo_nombre
            rol.clasificacion = nueva_clasificacion
            rol.save()
            messages.success(request, f"Rol '{rol.rol}' actualizado correctamente.")
            return redirect('lista_roles')

    return render(request, 'usuarios/rol/editar.html', {'rol': rol, 'clasificaciones': clasificaciones})


@login_required
def eliminar_rol(request, id_rol):
    rol = get_object_or_404(Rol, id_rol=id_rol)

    if request.method == 'POST':
        password_confirm = request.POST.get('password_confirm')

        if not request.user.check_password(password_confirm):
            # Agregamos "Acceso denegado" para que sea ALERTA CENTRAL ROJA
            messages.error(request, "Acceso denegado. Contraseña incorrecta. Acción cancelada.")
            return redirect('lista_roles')

        try:
            nombre_eliminado = rol.rol
            rol.delete()
            # Éxito (Toast Verde)
            messages.success(request, f"Rol '{nombre_eliminado}' eliminado definitivamente.")
        except ProtectedError:
            # Agregamos "Acceso denegado" para que sea ALERTA CENTRAL ROJA
            messages.error(request, f"Acceso denegado. No se puede eliminar '{rol.rol}' porque tiene usuarios vinculados.")

    return redirect('lista_roles')

@login_required
def cambiar_estado_rol_ajax(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            id_rol = data.get('id_rol')
            nuevo_estado = data.get('nuevo_estado')
            password = data.get('password')

            if not request.user.check_password(password):
                return JsonResponse({'success': False, 'message': 'Contraseña incorrecta.'})

            rol = Rol.objects.get(id_rol=id_rol)

            if rol.rol == 'ADMIN' and not nuevo_estado:
                return JsonResponse({'success': False, 'message': 'El rol ADMIN debe permanecer activo siempre.'})

            rol.estado_rol = nuevo_estado
            rol.save()

            accion = "activado" if nuevo_estado else "inactivado"
            return JsonResponse({
                'success': True,
                'message': f"Rol '{rol.rol}' {accion} correctamente."
            })

        except Rol.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Rol no encontrado.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Acceso no autorizado.'}, status=400)