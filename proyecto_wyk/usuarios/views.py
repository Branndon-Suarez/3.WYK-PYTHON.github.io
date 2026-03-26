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
                    messages.error(request,
                                   f"Acceso denegado. El rol '{usuario_db.rol_fk_usuario.rol}' está inactivo. Contacta al administrador.")
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


# ------------------------------ FUNCIONES DE ROLES (CRUD - SOLO ADMIN) ------------------------------

@login_required
def lista_roles(request):
    # Validamos por nombre de ROL
    if request.user.rol_fk_usuario.rol != 'ADMIN':
        messages.error(request, "Acceso denegado. No tienes permisos para gestionar roles.")
        return redirect('inicio')

    roles = Rol.objects.all().order_by('id_rol')
    return render(request, 'usuarios/rol/lista.html', {'roles': roles})


@login_required
def crear_rol(request):
    if request.user.rol_fk_usuario.rol != 'ADMIN':
        messages.error(request, "Acceso denegado. No tienes permisos para crear roles.")
        return redirect('inicio')

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
    if request.user.rol_fk_usuario.rol != 'ADMIN':
        messages.error(request, "Acceso denegado. No tienes permisos para editar roles.")
        return redirect('inicio')

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
    if request.user.rol_fk_usuario.rol != 'ADMIN':
        messages.error(request, "Acceso denegado. No tienes permisos para eliminar roles.")
        return redirect('inicio')

    rol = get_object_or_404(Rol, id_rol=id_rol)

    if request.method == 'POST':
        password_confirm = request.POST.get('password_confirm')

        if not request.user.check_password(password_confirm):
            messages.error(request, "Acceso denegado. Contraseña incorrecta. Acción cancelada.")
            return redirect('lista_roles')

        try:
            nombre_eliminado = rol.rol
            rol.delete()
            messages.success(request, f"Rol '{nombre_eliminado}' eliminado definitivamente.")
        except ProtectedError:
            messages.error(request,
                           f"Acceso denegado. No se puede eliminar '{rol.rol}' porque tiene usuarios vinculados.")

    return redirect('lista_roles')


@login_required
def cambiar_estado_rol_ajax(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.user.rol_fk_usuario.rol != 'ADMIN':
            return JsonResponse({'success': False, 'message': 'Acceso denegado.'})

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


# ------------------------------ FUNCIONES DE USUARIOS (CRUD - SOLO ADMIN) ------------------------------

@login_required
def lista_usuarios(request):
    if request.user.rol_fk_usuario.rol != 'ADMIN':
        messages.error(request, "Acceso denegado. No tienes permisos para gestionar usuarios.")
        return redirect('inicio')

    usuarios = Usuario.objects.all().select_related('rol_fk_usuario').order_by('id_usuario')
    roles_lista = Rol.objects.filter(estado_rol=True)
    return render(request, 'usuarios/usuario/lista.html', {
        'usuarios': usuarios,
        'roles_lista': roles_lista
    })


@login_required
def crear_usuario(request):
    if request.user.rol_fk_usuario.rol != 'ADMIN':
        messages.error(request, "Acceso denegado. No tienes permisos para crear usuarios.")
        return redirect('inicio')

    roles = Rol.objects.filter(estado_rol=True)

    if request.method == 'POST':
        num_doc = request.POST.get('num_doc')
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        password = request.POST.get('password')
        id_rol = request.POST.get('rol')

        if Usuario.objects.filter(num_doc=num_doc).exists():
            messages.error(request, f"Acceso denegado. El documento '{num_doc}' ya está registrado.")
        elif Usuario.objects.filter(email_usuario=email).exists():
            messages.error(request, f"Acceso denegado. El correo '{email}' ya está registrado.")
        else:
            try:
                rol_obj = Rol.objects.get(id_rol=id_rol)
                Usuario.objects.create_user(
                    num_doc=num_doc,
                    nombre=nombre,
                    email_usuario=email,
                    tel_usuario=telefono,
                    password=password,
                    rol_fk_usuario=rol_obj,
                    estado_usuario=True
                )
                messages.success(request, f"Usuario '{nombre}' creado exitosamente.")
                return redirect('lista_usuarios')
            except Exception as e:
                messages.error(request, f"Error al crear: {str(e)}")

    return render(request, 'usuarios/usuario/crear.html', {'roles': roles})


@login_required
def editar_usuario(request, id_usuario):
    if request.user.rol_fk_usuario.rol != 'ADMIN':
        messages.error(request, "Acceso denegado. No tienes permisos para editar usuarios.")
        return redirect('inicio')

    usuario_edit = get_object_or_404(Usuario, id_usuario=id_usuario)
    roles = Rol.objects.filter(estado_rol=True)

    if request.method == 'POST':
        num_doc = request.POST.get('num_doc')
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        id_rol = request.POST.get('rol')
        nueva_pass = request.POST.get('password')

        if Usuario.objects.filter(num_doc=num_doc).exclude(id_usuario=id_usuario).exists():
            messages.error(request, f"Acceso denegado. El documento '{num_doc}' ya pertenece a otro usuario.")
        elif Usuario.objects.filter(email_usuario=email).exclude(id_usuario=id_usuario).exists():
            messages.error(request, f"Acceso denegado. El correo '{email}' ya está registrado.")
        else:
            try:
                rol_obj = Rol.objects.get(id_rol=id_rol)
                usuario_edit.num_doc = num_doc
                usuario_edit.nombre = nombre
                usuario_edit.email_usuario = email
                usuario_edit.tel_usuario = telefono
                usuario_edit.rol_fk_usuario = rol_obj

                if nueva_pass and nueva_pass.strip():
                    usuario_edit.set_password(nueva_pass)

                usuario_edit.save()
                messages.success(request, f"Usuario '{usuario_edit.nombre}' actualizado.")
                return redirect('lista_usuarios')
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")

    return render(request, 'usuarios/usuario/editar.html', {
        'usuario': usuario_edit,
        'roles': roles
    })


@login_required
def eliminar_usuario(request, id_usuario):
    if request.user.rol_fk_usuario.rol != 'ADMIN':
        messages.error(request, "Acceso denegado. No tienes permisos para eliminar usuarios.")
        return redirect('inicio')

    usuario_del = get_object_or_404(Usuario, id_usuario=id_usuario)

    if request.method == 'POST':
        password_confirm = request.POST.get('password_confirm')

        if not request.user.check_password(password_confirm):
            messages.error(request, "Acceso denegado. Contraseña incorrecta. Acción cancelada.")
            return redirect('lista_usuarios')

        if usuario_del == request.user:
            messages.error(request, "Acceso denegado. No puedes eliminar tu propia cuenta.")
            return redirect('lista_usuarios')

        try:
            nombre_eliminado = usuario_del.nombre
            usuario_del.delete()
            messages.success(request, f"Usuario '{nombre_eliminado}' eliminado.")
        except ProtectedError:
            messages.error(request,
                           f"Acceso denegado. No se puede eliminar a '{usuario_del.nombre}' por registros asociados.")

    return redirect('lista_usuarios')


@login_required
def cambiar_estado_usuario_ajax(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.user.rol_fk_usuario.rol != 'ADMIN':
            return JsonResponse({'success': False, 'message': 'Acceso denegado.'})

        try:
            data = json.loads(request.body)
            id_u = data.get('id_usuario')
            nuevo_estado = data.get('nuevo_estado')
            password = data.get('password')

            if not request.user.check_password(password):
                return JsonResponse({'success': False, 'message': 'Acceso denegado. Contraseña incorrecta.'})

            usuario = Usuario.objects.get(id_usuario=id_u)

            if usuario == request.user and not nuevo_estado:
                return JsonResponse({'success': False, 'message': 'No puedes desactivar tu propia cuenta.'})

            usuario.estado_usuario = nuevo_estado
            usuario.save()

            accion = "activado" if nuevo_estado else "inactivado"
            return JsonResponse({
                'success': True,
                'message': f"Usuario '{usuario.nombre}' {accion} correctamente."
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Acceso no autorizado.'}, status=400)