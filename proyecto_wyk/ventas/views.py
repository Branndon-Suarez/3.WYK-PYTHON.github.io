from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
import json

from .models import Venta, DetalleVenta
from inventario.models import Producto
from .forms import VentaForm, DetalleVentaFormSet


# ------------------------------ GESTIÓN DE VENTAS (CRUD) ------------------------------

@login_required
def lista_ventas(request):
    """ Lista las ventas. El ADMIN/CAJERO ve todas, otros roles ven las del día """
    rol_usuario = request.user.rol_fk_usuario.rol
    queryset = Venta.objects.all().order_by('-fecha_hora_venta')

    if rol_usuario in ['ADMIN', 'CAJERO']:
        ventas = queryset
    else:
        # Filtro de seguridad para que personal vea solo lo de hoy
        ventas = queryset.filter(fecha_hora_venta__date=timezone.now().date())

    return render(request, 'ventas/lista.html', {'ventas': ventas})


@login_required
def crear_venta(request):
    """
    Registra una nueva orden de venta.
    Si es Mesero: estado PENDIENTE.
    Si es Cajero/Admin: estado PAGADA/ENTREGADO y resta stock inmediatamente.
    """
    productos = Producto.objects.filter(estado_producto=True)
    rol_usuario = request.user.rol_fk_usuario.rol

    if request.method == 'POST':
        form = VentaForm(request.POST)
        formset = DetalleVentaFormSet(request.POST, prefix='detalles_set')

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # 1. Guardar Cabecera
                    nueva_venta = form.save(commit=False)
                    nueva_venta.id_usuario_fk_venta = request.user
                    nueva_venta.fecha_hora_venta = timezone.now()

                    # Lógica de estados según rol
                    if rol_usuario in ['ADMIN', 'CAJERO']:
                        nueva_venta.estado_pedido = 'ENTREGADO'
                        nueva_venta.estado_pago = 'PAGADA'
                    else:
                        # Meseros solo pueden crear ventas PENDIENTES
                        nueva_venta.estado_pedido = 'PENDIENTE'
                        nueva_venta.estado_pago = 'PENDIENTE'

                    nueva_venta.total_venta = 0
                    nueva_venta.save()

                    # 2. Guardar Detalles y manejar Stock
                    detalles = formset.save(commit=False)
                    total_calculado = 0

                    for detalle in detalles:
                        producto = detalle.id_producto_fk_det_venta

                        # Si es venta directa (Cajero/Admin), validamos y restamos stock de inmediato
                        if rol_usuario in ['ADMIN', 'CAJERO']:
                            if producto.cant_exist_producto < detalle.cantidad:
                                raise ValueError(f"Stock insuficiente para {producto.nombre_producto}")

                            producto.cant_exist_producto -= detalle.cantidad
                            producto.save()

                        detalle.id_venta_fk_det_venta = nueva_venta
                        detalle.sub_total = producto.valor_unitario_product * detalle.cantidad
                        total_calculado += detalle.sub_total
                        detalle.save()

                    # 3. Actualizar total final
                    nueva_venta.total_venta = total_calculado
                    nueva_venta.save()

                    messages.success(request, f"Venta #{nueva_venta.id_venta} registrada correctamente.")
                    return redirect('lista_ventas')
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error en base de datos: {str(e)}")
        else:
            for error in form.non_field_errors(): messages.error(request, error)
            for field in form:
                for error in field.errors: messages.error(request, f"{field.label}: {error}")
    else:
        form = VentaForm()
        formset = DetalleVentaFormSet(prefix='detalles_set')

    return render(request, 'ventas/crear.html', {
        'form': form,
        'formset': formset,
        'productos': productos
    })


@login_required
def detalle_venta(request, id_venta):
    """ Muestra la información completa de la venta y sus productos """
    venta = get_object_or_404(Venta, id_venta=id_venta)
    detalles = venta.detalles.all()
    return render(request, 'ventas/detalle.html', {
        'venta': venta,
        'detalles': detalles
    })


# ------------------------------ ACCIONES AJAX (FLUJO DE ESTADOS) ------------------------------

@login_required
def entregar_venta_ajax(request):
    """ Acción del Mesero/Admin: Cambia PENDIENTE -> ENTREGADO """
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            id_v = data.get('id_venta')
            venta = get_object_or_404(Venta, id_venta=id_v)

            # Verificación de permiso: El mesero no puede cobrar, solo entregar
            if venta.estado_pago != 'PENDIENTE':
                return JsonResponse({'success': False, 'message': 'Solo se pueden entregar pedidos pendientes de pago.'})

            venta.estado_pedido = 'ENTREGADO'
            venta.save()

            # Respondemos directamente para que JS maneje el SweetAlert sin persistir mensajes en sesión
            return JsonResponse({'success': True, 'message': 'Pedido marcado como ENTREGADO. Ya puede ser cobrado.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False}, status=400)


@login_required
def finalizar_venta_ajax(request):
    """ Acción del Cajero/Admin: Cambia ENTREGADO -> PAGADA y DESCUENTA stock """
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Seguridad de Rol: Solo CAJERO o ADMIN pueden realizar el cobro final
        if request.user.rol_fk_usuario.rol not in ['ADMIN', 'CAJERO']:
            return JsonResponse({'success': False, 'message': 'No tienes permisos para registrar pagos.'})

        try:
            data = json.loads(request.body)
            id_v = data.get('id_venta')

            with transaction.atomic():
                venta = get_object_or_404(Venta, id_venta=id_v)

                if venta.estado_pedido != 'ENTREGADO':
                    return JsonResponse(
                        {'success': False, 'message': 'El pedido debe marcarse como ENTREGADO antes de cobrar.'})

                if venta.estado_pago == 'PAGADA':
                    return JsonResponse({'success': False, 'message': 'Esta venta ya fue pagada.'})

                # 1. Validar y Restar stock en el momento del cobro
                detalles = venta.detalles.all()
                for item in detalles:
                    producto = item.id_producto_fk_det_venta
                    if producto.cant_exist_producto < item.cantidad:
                        return JsonResponse({
                            'success': False,
                            'message': f"Stock insuficiente para {producto.nombre_producto} (Disponible: {producto.cant_exist_producto})."
                        })

                    producto.cant_exist_producto -= item.cantidad
                    producto.save()

                # 2. Finalizar
                venta.estado_pago = 'PAGADA'
                venta.fecha_cambio_estado = timezone.now()
                venta.save()

            return JsonResponse({'success': True, 'message': 'Venta PAGADA e inventario actualizado correctamente.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f"Error: {str(e)}"})
    return JsonResponse({'success': False}, status=400)


@login_required
def cancelar_venta_ajax(request):
    """ Cancela la venta. Requiere contraseña. Si ya estaba PAGADA, devuelve el stock """
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            # Solo el ADMIN o alguien con la clave puede anular ventas
            if not request.user.check_password(data.get('password')):
                return JsonResponse({'success': False, 'message': 'Contraseña incorrecta.'})

            venta = get_object_or_404(Venta, id_venta=data.get('id_venta'))

            if venta.estado_pago == 'CANCELADA':
                return JsonResponse({'success': False, 'message': 'Esta venta ya se encuentra cancelada.'})

            with transaction.atomic():
                # Si estaba PAGADA, revertimos el stock al almacén
                if venta.estado_pago == 'PAGADA':
                    for item in venta.detalles.all():
                        producto = item.id_producto_fk_det_venta
                        producto.cant_exist_producto += item.cantidad
                        producto.save()

                venta.estado_pago = 'CANCELADA'
                venta.estado_pedido = 'CANCELADO'
                venta.fecha_cambio_estado = timezone.now()
                venta.save()

            return JsonResponse({'success': True, 'message': 'Venta anulada correctamente. El stock ha sido devuelto.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False}, status=400)