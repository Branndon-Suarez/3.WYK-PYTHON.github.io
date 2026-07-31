from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum

from .models import Venta, DetalleVenta
from inventario.models import Producto, MateriaPrima
from recetas.models import Receta, DetalleReceta
from compras.models import Compra, DetalleCompraMateriaPrima, Proveedor
from produccion.models import (
    Produccion,
    DetalleProduccion,
    OrdenAbastecimiento,
    TipoOrdenAbastecimiento,
    TipoOrigenAbastecimiento
)


@transaction.atomic
def procesar_venta_con_abastecimiento(usuario, form_venta, formset_detalles):
    """
    Procesa el registro de la venta. Si falta stock de producto, crea automáticamente
    la Orden de Producción. Si además faltan materias primas según la receta,
    crea automáticamente la Orden de Compra.
    """
    rol_usuario = usuario.rol_fk_usuario.rol

    # 1. Instanciar y preparar la venta
    nueva_venta = form_venta.save(commit=False)
    nueva_venta.id_usuario_fk_venta = usuario
    nueva_venta.fecha_hora_venta = timezone.now()

    if rol_usuario in ['ADMIN', 'CAJERO']:
        nueva_venta.estado_pedido = Venta.EstadoPedido.ENTREGADO
        nueva_venta.estado_pago = Venta.EstadoPago.PAGADA
    else:
        nueva_venta.estado_pedido = Venta.EstadoPedido.PENDIENTE
        nueva_venta.estado_pago = Venta.EstadoPago.PENDIENTE

    nueva_venta.total_venta = 0
    nueva_venta.save()

    detalles = formset_detalles.save(commit=False)
    total_calculado = 0

    for detalle in detalles:
        producto = detalle.id_producto_fk_det_venta
        cant_solicitada = detalle.cantidad

        # Calcular stock disponible real excluyendo pedidos pendientes
        apartado = DetalleVenta.objects.filter(
            id_producto_fk_det_venta=producto,
            id_venta_fk_det_venta__estado_pago=Venta.EstadoPago.PENDIENTE
        ).aggregate(Sum('cantidad'))['cantidad__sum'] or 0

        stock_disponible = producto.cant_exist_producto - apartado

        # Guardar el detalle de la venta
        detalle.id_venta_fk_det_venta = nueva_venta
        detalle.sub_total = producto.valor_unitario_product * cant_solicitada
        total_calculado += detalle.sub_total
        detalle.save()

        # Si es ADMIN o CAJERO y hay stock suficiente, descuenta directamente
        if rol_usuario in ['ADMIN', 'CAJERO'] and stock_disponible >= cant_solicitada:
            producto.cant_exist_producto -= cant_solicitada
            producto.save()
            continue

        # EVALUACIÓN DE FALTANTES DE PRODUCTO
        if stock_disponible < cant_solicitada:
            cant_faltante_prod = cant_solicitada - max(0, stock_disponible)

            # Si es ADMIN/CAJERO, se agota lo que queda en bodega física
            if rol_usuario in ['ADMIN', 'CAJERO']:
                producto.cant_exist_producto = max(0, producto.cant_exist_producto - cant_solicitada)
                producto.save()

            # Obtener Receta Única Activa del Producto
            receta = Receta.objects.filter(
                id_producto_fk_receta=producto,
                estado_receta=True
            ).first()

            if not receta:
                raise ValueError(
                    f"El producto '{producto.nombre_producto}' no tiene una receta activa configurada para abastecimiento."
                )

            # A) CREAR ORDEN DE PRODUCCIÓN
            produccion = Produccion.objects.create(
                nombre_produccion=f"Prod. Auto - Venta #{nueva_venta.id_venta}",
                fecha_hora_produccion=timezone.now(),
                categoria_produccion=producto.tipo_producto,
                cant_produccion=cant_faltante_prod,
                descripcion_produccion=f"Generado automáticamente por faltante de {cant_faltante_prod} un. en Venta #{nueva_venta.id_venta}",
                id_producto_fk_produccion=producto,
                id_receta_fk_produccion=receta,
                id_usuario_fk_produccion=usuario,
                estado_produccion=Produccion.EstadoProduccion.PENDIENTE
            )

            # B) REGISTRAR TRAZABILIDAD EN ORDEN DE ABASTECIMIENTO (PRODUCCIÓN)
            OrdenAbastecimiento.objects.create(
                tipo_orden=TipoOrdenAbastecimiento.PRODUCCION,
                origen_orden=TipoOrigenAbastecimiento.FALTANTE_VENTA,
                id_venta_fk_abastecimiento=nueva_venta,
                id_produccion_fk_abastecimiento=produccion,
                id_usuario_fk_abastecimiento=usuario,
                observacion=f"Abastecimiento automático de {cant_faltante_prod} un. de {producto.nombre_producto}"
            )

            # C) EVALUACIÓN DE MATERIAS PRIMAS (RECETA vs BODEGA)
            insumos_receta = DetalleReceta.objects.filter(id_receta_fk_det_rec=receta)

            for insumo in insumos_receta:
                materia_prima = insumo.id_materia_prima_fk_det_rec

                # Cálculo proporcional exacto según la cantidad base de la receta
                cant_mat_requerida = (
                    Decimal(insumo.cantidad_insumo_base) / Decimal(receta.cantidad_base)
                ) * Decimal(cant_faltante_prod)

                # Registrar detalle del requerimiento para producción
                DetalleProduccion.objects.create(
                    id_produccion_fk_det_produc=produccion,
                    id_materia_prima_fk_det_produc=materia_prima,
                    cantidad_requerida=cant_mat_requerida
                )

                # Si la Materia Prima en Bodega es insuficiente
                if materia_prima.cantidad_exist_mat_prima < cant_mat_requerida:
                    cant_faltante_mat = cant_mat_requerida - Decimal(materia_prima.cantidad_exist_mat_prima)

                    # Buscar un proveedor activo (o el primero registrado)
                    proveedor_defecto = Proveedor.objects.filter(estado_proveedor=True).first()
                    if not proveedor_defecto:
                        raise ValueError(
                            "No hay un proveedor activo configurado en el sistema para realizar la compra de materia prima."
                        )

                    # D) CREAR ORDEN DE COMPRA DE MATERIA PRIMA
                    compra = Compra.objects.create(
                        fecha_hora_compra=timezone.now(),
                        tipo=Compra.TipoCompra.MATERIA_PRIMA,
                        total_compra=0,  # Se liquida al cotizar/recibir la factura
                        descripcion_compra=f"Compra automática por faltante en Venta #{nueva_venta.id_venta}",
                        id_usuario_fk_compra=usuario,
                        id_proveedor_fk_compra=proveedor_defecto,
                        estado_factura_compra=Compra.EstadoPago.PENDIENTE
                    )

                    DetalleCompraMateriaPrima.objects.create(
                        cantidad_mat_prima_comprada=cant_faltante_mat,
                        sub_total_mat_prima_comprada=0,
                        id_compra_fk_det_compra_mat_prima=compra,
                        id_mat_prima_fk_det_compra_mat_prima=materia_prima,
                        estado_det_compra_mat_prima=True
                    )

                    # E) REGISTRAR TRAZABILIDAD EN ORDEN DE ABASTECIMIENTO (COMPRA)
                    OrdenAbastecimiento.objects.create(
                        tipo_orden=TipoOrdenAbastecimiento.COMPRA,
                        origen_orden=TipoOrigenAbastecimiento.FALTANTE_VENTA,
                        id_venta_fk_abastecimiento=nueva_venta,
                        id_compra_fk_abastecimiento=compra,
                        id_usuario_fk_abastecimiento=usuario,
                        observacion=f"Compra automática por faltante de {cant_faltante_mat} {materia_prima.presentacion_mat_prima} de {materia_prima.nombre_materia_prima}"
                    )

    # Actualizar total de la venta
    nueva_venta.total_venta = total_calculado
    nueva_venta.save()

    return nueva_venta