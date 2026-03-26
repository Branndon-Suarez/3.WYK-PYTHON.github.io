from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import ProtectedError
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.http import JsonResponse
import json
from .models import Rol, Usuario
from django.db import connection

# IMPORTANTE: Ahora importamos los nuevos formularios
from .forms import LoginForm, RolForm, UsuarioForm

# ------------------------------ AUTENTICACIÓN ------------------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    if request.method == 'POST':
        num_doc_post = request.POST.get('username')
        password_post = request.POST.get('password')

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

        user = authenticate(request, num_doc=num_doc_post, password=password_post)

        if user is not None:
            auth_login(request, user)
            return redirect('inicio')
        else:
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

    form = RolForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f"Rol '{form.cleaned_data['rol']}' creado correctamente.")
            return redirect('lista_roles')
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
            for field in form:
                for error in field.errors:
                    messages.error(request, error)

    return render(request, 'usuarios/rol/crear.html', {
        'clasificaciones': Rol.Clasificacion.choices,
        'form': form
    })


@login_required
def editar_rol(request, id_rol):
    if request.user.rol_fk_usuario.rol != 'ADMIN':
        messages.error(request, "Acceso denegado. No tienes permisos para editar roles.")
        return redirect('inicio')

    rol = get_object_or_404(Rol, id_rol=id_rol)
    form = RolForm(request.POST or None, instance=rol)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f"Rol '{rol.rol}' actualizado correctamente.")
            return redirect('lista_roles')
        else:
            for field in form:
                for error in field.errors:
                    messages.error(request, error)

    return render(request, 'usuarios/rol/editar.html', {
        'rol': rol,
        'clasificaciones': Rol.Clasificacion.choices,
        'form': form
    })


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
            messages.error(request, f"Acceso denegado. No se puede eliminar '{rol.rol}' porque tiene usuarios vinculados.")

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
            return JsonResponse({'success': True, 'message': f"Rol '{rol.rol}' {accion} correctamente."})
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
    roles_lista = Rol.objects.all().order_by('rol')

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
    form = UsuarioForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            nuevo_usuario = form.save(commit=False)
            nuevo_usuario.set_password(request.POST.get('password'))
            nuevo_usuario.estado_usuario = True
            nuevo_usuario.save()
            messages.success(request, f"Usuario '{nuevo_usuario.nombre}' creado exitosamente.")
            return redirect('lista_usuarios')
        else:
            for field in form:
                for error in field.errors:
                    messages.error(request, error)

    return render(request, 'usuarios/usuario/crear.html', {'roles': roles, 'form': form})


@login_required
def editar_usuario(request, id_usuario):
    if request.user.rol_fk_usuario.rol != 'ADMIN':
        messages.error(request, "Acceso denegado. No tienes permisos para editar usuarios.")
        return redirect('inicio')

    usuario_edit = get_object_or_404(Usuario, id_usuario=id_usuario)
    roles = Rol.objects.filter(estado_rol=True)
    form = UsuarioForm(request.POST or None, instance=usuario_edit)

    if request.method == 'POST':
        if form.is_valid():
            usuario_actualizado = form.save(commit=False)
            nueva_pass = request.POST.get('password')
            if nueva_pass and nueva_pass.strip():
                usuario_actualizado.set_password(nueva_pass)
            usuario_actualizado.save()
            messages.success(request, f"Usuario '{usuario_actualizado.nombre}' actualizado.")
            return redirect('lista_usuarios')
        else:
            for field in form:
                for error in field.errors:
                    messages.error(request, error)

    return render(request, 'usuarios/usuario/editar.html', {
        'usuario': usuario_edit,
        'roles': roles,
        'form': form
    })


@login_required
def eliminar_usuario(request, id_usuario):
    if request.user.rol_fk_usuario.rol != 'ADMIN':
        messages.error(request, "Acceso denegado. No tienes permisos.")
        return redirect('inicio')

    usuario_del = get_object_or_404(Usuario, id_usuario=id_usuario)

    if request.method == 'POST':
        password_confirm = request.POST.get('password_confirm')
        if not request.user.check_password(password_confirm):
            messages.error(request, "Contraseña de administrador incorrecta.")
            return redirect('lista_usuarios')

        if usuario_del == request.user:
            messages.error(request, "No puedes eliminar tu propia cuenta.")
            return redirect('lista_usuarios')

        try:
            nombre_eliminado = usuario_del.nombre
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM usuario WHERE id_usuario = %s", [id_usuario])
            messages.success(request, f"Usuario '{nombre_eliminado}' eliminado correctamente.")
        except Exception:
            messages.error(request, f"No se puede eliminar a '{usuario_del.nombre}' porque tiene registros asociados.")

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
            return JsonResponse({'success': True, 'message': f"Usuario '{usuario.nombre}' {accion} correctamente."})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Acceso no autorizado.'}, status=400)