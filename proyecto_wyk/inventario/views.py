from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import ProtectedError
from django.http import JsonResponse
import json

from .models import Producto, MateriaPrima, AjusteInventario, AjusteIventarioMatPrima
from .forms import ProductoForm # Asegúrate de crear este formulario en forms.py

# ------------------------------ PRODUCTOS ------------------------------

@login_required
def lista_productos(request):
    # Solo permitimos ver si es ADMIN o tiene permisos (ajusta según tu lógica)
    productos = Producto.objects.all().order_by('id_producto')
    return render(request, 'inventario/producto/lista.html', {'productos': productos})


@login_required
def crear_producto(request):
    form = ProductoForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            nuevo_producto = form.save(commit=False)
            # Asignación automática del usuario que crea el registro
            nuevo_producto.id_usuario_fk_producto = request.user
            nuevo_producto.save()
            messages.success(request, f"Producto '{nuevo_producto.nombre_producto}' creado correctamente.")
            return redirect('lista_productos')
        else:
            for field in form:
                for error in field.errors:
                    messages.error(request, error)

    return render(request, 'inventario/producto/crear.html', {'form': form})


@login_required
def editar_producto(request, id_producto):
    producto = get_object_or_404(Producto, id_producto=id_producto)
    # Importante: request.FILES permite actualizar la imagen
    form = ProductoForm(request.POST or None, request.FILES or None, instance=producto)

    if request.method == 'POST':
        if form.is_valid():
            producto_editado = form.save()
            messages.success(request, f"Producto '{producto_editado.nombre_producto}' actualizado correctamente.")
            return redirect('lista_productos')
        else:
            for field in form:
                for error in field.errors:
                    messages.error(request, error)

    return render(request, 'inventario/producto/editar.html', {
        'form': form,
        'producto': producto
    })


@login_required
def eliminar_producto(request, id_producto):
    producto = get_object_or_404(Producto, id_producto=id_producto)

    if request.method == 'POST':
        password_confirm = request.POST.get('password_confirm')
        if not request.user.check_password(password_confirm):
            messages.error(request, "Acceso denegado. Contraseña incorrecta.")
            return redirect('lista_productos')

        try:
            nombre_eliminado = producto.nombre_producto
            producto.delete()
            messages.success(request, f"Producto '{nombre_eliminado}' eliminado definitivamente.")
        except ProtectedError:
            messages.error(request, f"No se puede eliminar '{producto.nombre_producto}' porque tiene registros asociados (ventas o ajustes).")

    return redirect('lista_productos')


@login_required
def cambiar_estado_producto_ajax(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            id_prod = data.get('id_producto')
            nuevo_estado = data.get('nuevo_estado')
            password = data.get('password')

            if not request.user.check_password(password):
                return JsonResponse({'success': False, 'message': 'Contraseña incorrecta.'})

            producto = Producto.objects.get(id_producto=id_prod)
            producto.estado_producto = nuevo_estado
            producto.save()

            accion = "activado" if nuevo_estado else "inactivado"
            return JsonResponse({'success': True, 'message': f"Producto '{producto.nombre_producto}' {accion}."})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Acceso no autorizado.'}, status=400)


# ------------------------------ MATERIA PRIMA (Esqueleto) ------------------------------

# ------------------------------ MATERIA PRIMA ------------------------------

@login_required
def lista_materia_prima(request):
    materias = MateriaPrima.objects.all().order_by('id_materia_prima')
    return render(request, 'inventario/materia_prima/lista.html', {'materias': materias})


@login_required
def crear_materia_prima(request):
    from .forms import MateriaPrimaForm  # Importación local para evitar ciclos
    form = MateriaPrimaForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            nueva_mat = form.save(commit=False)
            nueva_mat.id_usuario_fk_mat_prima = request.user
            nueva_mat.save()
            messages.success(request, f"Materia prima '{nueva_mat.nombre_materia_prima}' registrada.")
            return redirect('lista_materia_prima')
    return render(request, 'inventario/materia_prima/crear.html', {'form': form})


@login_required
def editar_materia_prima(request, id_materia_prima):
    materia = get_object_or_404(MateriaPrima, id_materia_prima=id_materia_prima)
    from .forms import MateriaPrimaForm
    form = MateriaPrimaForm(request.POST or None, instance=materia)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Materia prima actualizada.")
            return redirect('lista_materia_prima')
    return render(request, 'inventario/materia_prima/editar.html', {'form': form, 'materia': materia})


@login_required
def eliminar_materia_prima(request, id_materia_prima):
    materia = get_object_or_404(MateriaPrima, id_materia_prima=id_materia_prima)
    if request.method == 'POST':
        password_confirm = request.POST.get('password_confirm')
        if not request.user.check_password(password_confirm):
            messages.error(request, "Contraseña incorrecta.")
            return redirect('lista_materia_prima')
        materia.delete()
        messages.success(request, "Materia prima eliminada.")
    return redirect('lista_materia_prima')


@login_required
def cambiar_estado_materia_prima_ajax(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            materia = MateriaPrima.objects.get(id_materia_prima=data.get('id_materia_prima'))
            if not request.user.check_password(data.get('password')):
                return JsonResponse({'success': False, 'message': 'Contraseña incorrecta.'})

            materia.estado_materia_prima = data.get('nuevo_estado')
            materia.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False}, status=400)


# ------------------------------ AJUSTES (Solo Lista y Crear) ------------------------------

@login_required
def lista_ajustes_producto(request):
    ajustes = AjusteInventario.objects.all().select_related('id_prod_fk_ajuste', 'id_usuario_fk_ajuste').order_by('-fecha_ajuste')
    return render(request, 'inventario/ajustes/lista_productos.html', {'ajustes': ajustes})


@login_required
def crear_ajuste_producto(request):
    # Lógica para registrar un movimiento de pérdida/daño
    pass

@login_required
def lista_ajustes_materia_prima(request):
    ajustes = AjusteIventarioMatPrima.objects.all().order_by('-fecha_ajust_mat')
    return render(request, 'inventario/ajustes/lista_materia.html', {'ajustes': ajustes})

@login_required
def crear_ajuste_materia_prima(request):
    pass