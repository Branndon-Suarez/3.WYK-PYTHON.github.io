# C:\xampp\htdocs\3.WYK-PYTHON.github.io\proyecto_wyk\compras\views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import ProtectedError
from django.http import JsonResponse
import json
from .models import Proveedor
from .forms import ProveedorForm


# ------------------------------ GESTIÓN DE PROVEEDORES (CRUD) ------------------------------

@login_required
def lista_proveedores(request):
    """ Lista todos los proveedores ordenados por nombre """
    if request.user.rol_fk_usuario.rol not in ['ADMIN', 'OPERARIO']:
        messages.error(request, "Acceso denegado. No tienes permisos para gestionar proveedores.")
        return redirect('inicio')

    proveedores = Proveedor.objects.all().order_by('nombre_proveedor')
    return render(request, 'compras/proveedores/lista.html', {'proveedores': proveedores})


@login_required
def crear_proveedor(request):
    """ Crea un nuevo proveedor vinculándolo al usuario actual """
    if request.user.rol_fk_usuario.rol != 'ADMIN':
        messages.error(request, "Acceso denegado. Solo administradores pueden crear proveedores.")
        return redirect('lista_proveedores')

    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            nuevo_proveedor = form.save(commit=False)
            nuevo_proveedor.id_usuario_fk_proveedor = request.user
            nuevo_proveedor.estado_proveedor = True
            nuevo_proveedor.save()
            messages.success(request, f"Proveedor '{nuevo_proveedor.nombre_proveedor}' creado correctamente.")
            return redirect('lista_proveedores')
        else:
            # Captura errores de validación (como nombre duplicado definido en el form)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = ProveedorForm()

    return render(request, 'compras/proveedores/crear.html', {'form': form})


@login_required
def editar_proveedor(request, cedula_proveedor):
    """ Edita la información de un proveedor existente """
    if request.user.rol_fk_usuario.rol != 'ADMIN':
        messages.error(request, "Acceso denegado. No tienes permisos para editar proveedores.")
        return redirect('lista_proveedores')

    proveedor = get_object_or_404(Proveedor, cedula_proveedor=cedula_proveedor)

    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, f"Proveedor '{proveedor.nombre_proveedor}' actualizado correctamente.")
            return redirect('lista_proveedores')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = ProveedorForm(instance=proveedor)

    return render(request, 'compras/proveedores/editar.html', {
        'proveedor': proveedor,
        'form': form
    })


@login_required
def eliminar_proveedor(request, cedula_proveedor):
    """ Elimina un proveedor si no tiene compras asociadas """
    if request.user.rol_fk_usuario.rol != 'ADMIN':
        messages.error(request, "Acceso denegado.")
        return redirect('lista_proveedores')

    proveedor = get_object_or_404(Proveedor, cedula_proveedor=cedula_proveedor)

    if request.method == 'POST':
        password_confirm = request.POST.get('password_confirm')

        if not request.user.check_password(password_confirm):
            messages.error(request, "Acceso denegado. Contraseña incorrecta. Acción cancelada.")
            return redirect('lista_proveedores')

        try:
            nombre_eliminado = proveedor.nombre_proveedor
            proveedor.delete()
            messages.success(request, f"Proveedor '{nombre_eliminado}' eliminado definitivamente.")
        except ProtectedError:
            messages.error(request,
                           f"Acceso denegado. '{proveedor.nombre_proveedor}' tiene registros de compras asociados.")

    return redirect('lista_proveedores')


# ------------------------------ SEGURIDAD AJAX ------------------------------

@login_required
def cambiar_estado_proveedor_ajax(request):
    """ Activa o inactiva un proveedor mediante AJAX """
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.user.rol_fk_usuario.rol != 'ADMIN':
            return JsonResponse({'success': False, 'message': 'Acceso denegado.'})

        try:
            data = json.loads(request.body)
            cedula = data.get('cedula_proveedor')
            nuevo_estado = data.get('nuevo_estado')
            password = data.get('password')

            if not request.user.check_password(password):
                return JsonResponse({'success': False, 'message': 'Acceso denegado. Contraseña incorrecta.'})

            proveedor = Proveedor.objects.get(cedula_proveedor=cedula)
            proveedor.estado_proveedor = nuevo_estado
            proveedor.save()

            accion = "activado" if nuevo_estado else "inactivado"
            return JsonResponse({
                'success': True,
                'message': f"Proveedor '{proveedor.nombre_proveedor}' {accion} correctamente."
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Acceso no autorizado.'}, status=400)