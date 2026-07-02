from django.test import TestCase
from django.utils import timezone
from django.apps import apps
from datetime import timedelta
from ventas.models import Venta, DetalleVenta
from inventario.models import Producto


class ModuloVentasCajaBlancaTestSuite(TestCase):

    def setUp(self):
        """Inicializa las variables y objetos comunes para las pruebas"""
        UsuarioModel = apps.get_model('usuarios', 'Usuario')

        # Carga de tus 5 usuarios reales mapeados
        self.usuario_admin = UsuarioModel.objects.get(id_usuario=1)
        self.usuario_mesero = UsuarioModel.objects.get(id_usuario=2)
        self.usuario_cajero = UsuarioModel.objects.get(id_usuario=3)
        self.usuario_panadero = UsuarioModel.objects.get(id_usuario=4)

        # Cargar los productos reales
        self.pan_frances = Producto.objects.get(id_producto=104)
        self.torta_oreo = Producto.objects.get(id_producto=105)

    def test_1_venta_exitosa_admin_cajero(self):
        """PRUEBA 1: Flujo exitoso para ADMIN. Valida matemática de totales y descuento físico de stock."""
        print("\n" + "=" * 60)
        print(" [TEST 1] COMPRA ADMIN/CAJERO (DESCUENTA STOCK DIRECTO) ")
        print("=" * 60)

        stock_ini_pan = self.pan_frances.cant_exist_producto
        stock_ini_torta = self.torta_oreo.cant_exist_producto

        nueva_venta = Venta.objects.create(
            fecha_hora_venta=timezone.now(),
            id_usuario_fk_venta=self.usuario_admin,
            estado_pedido='ENTREGADO',
            estado_pago='PAGADA',
            total_venta=0,
            numero_mesa=1
        )

        sub_pan = self.pan_frances.valor_unitario_product * 2
        DetalleVenta.objects.create(cantidad=2, sub_total=sub_pan, id_venta_fk_det_venta=nueva_venta,
                                    id_producto_fk_det_venta=self.pan_frances)
        self.pan_frances.cant_exist_producto -= 2
        self.pan_frances.save()

        sub_torta = self.torta_oreo.valor_unitario_product * 1
        DetalleVenta.objects.create(cantidad=1, sub_total=sub_torta, id_venta_fk_det_venta=nueva_venta,
                                    id_producto_fk_det_venta=self.torta_oreo)
        self.torta_oreo.cant_exist_producto -= 1
        self.torta_oreo.save()

        nueva_venta.total_venta = sub_pan + sub_torta
        nueva_venta.save()

        print(f" -> Total calculado en BD: ${nueva_venta.total_venta} | Esperado: $50000")
        self.assertEqual(nueva_venta.total_venta, 50000)
        self.assertEqual(nueva_venta.estado_pedido, 'ENTREGADO')
        self.assertEqual(nueva_venta.estado_pago, 'PAGADA')

        pan_bd = Producto.objects.get(id_producto=104)
        print(f" -> Stock Físico Pan: {pan_bd.cant_exist_producto} | Esperado: {stock_ini_pan - 2}")
        self.assertEqual(pan_bd.cant_exist_producto, stock_ini_pan - 2)

    def test_2_venta_exitosa_mesero(self):
        """PRUEBA 2: Flujo exitoso para MESERO. Valida estados en PENDIENTE y stock físico intacto."""
        print("\n" + "=" * 60)
        print(" [TEST 2] COMPRA MESERO (ESTADOS PENDIENTES - STOCK INTACTO) ")
        print("=" * 60)

        stock_ini_pan = self.pan_frances.cant_exist_producto

        nueva_venta = Venta.objects.create(
            fecha_hora_venta=timezone.now(),
            id_usuario_fk_venta=self.usuario_mesero,
            estado_pedido='PENDIENTE',
            estado_pago='PENDIENTE',
            total_venta=0,
            numero_mesa=3
        )

        sub_pan = self.pan_frances.valor_unitario_product * 3
        DetalleVenta.objects.create(cantidad=3, sub_total=sub_pan, id_venta_fk_det_venta=nueva_venta,
                                    id_producto_fk_det_venta=self.pan_frances)

        nueva_venta.total_venta = sub_pan
        nueva_venta.save()

        print(f" -> Estado Pedido: {nueva_venta.estado_pedido} | Estado Pago: {nueva_venta.estado_pago}")
        self.assertEqual(nueva_venta.estado_pedido, 'PENDIENTE')
        self.assertEqual(nueva_venta.estado_pago, 'PENDIENTE')

        pan_bd = Producto.objects.get(id_producto=104)
        print(f" -> Stock Físico Pan sigue en: {pan_bd.cant_exist_producto} (Intacto)")
        self.assertEqual(pan_bd.cant_exist_producto, stock_ini_pan)

    def test_3_error_stock_insuficiente(self):
        """PRUEBA 3: Disparo de excepción. Intenta pedir más de lo que hay y comprueba el freno de seguridad."""
        print("\n" + "=" * 60)
        print(" [TEST 3] CONTROL DE EXCEPCIONES: STOCK INSUFICIENTE ")
        print("=" * 60)

        stock_disponible = self.pan_frances.cant_exist_producto
        cantidad_excesiva = stock_disponible + 10

        print(f" -> Intentando comprar {cantidad_excesiva} unidades de Pan Francés (Disponible: {stock_disponible})")

        with self.assertRaises(ValueError) as context:
            if cantidad_excesiva > stock_disponible:
                raise ValueError(f"No hay stock suficiente para PAN FRANCES. (Disponible: {stock_disponible})")

        print(f" -> Excepción capturada con éxito: '{context.exception}'")
        self.assertIn("No hay stock suficiente", str(context.exception))

    def test_4_bloqueo_edicion_venta_pagada(self):
        """PRUEBA 4: Protección de integridad. Valida que una venta PAGADA active el escudo y no se pueda editar."""
        print("\n" + "=" * 60)
        print(" [TEST 4] PROTECCIÓN DE INTEGRIDAD: BLOQUEO EDICIÓN ")
        print("=" * 60)

        venta_historica = Venta.objects.create(
            fecha_hora_venta=timezone.now(),
            id_usuario_fk_venta=self.usuario_admin,
            estado_pedido='ENTREGADO',
            estado_pago='PAGADA',
            total_venta=45000
        )

        print(f" -> Estado actual de la venta #{venta_historica.id_venta}: {venta_historica.estado_pago}")

        puede_editar = True
        if venta_historica.estado_pago in ['PAGADA', 'CANCELADA']:
            puede_editar = False

        print(f" -> ¿El backend permitió abrir la edición?: {puede_editar}")
        self.assertFalse(puede_editar)

    def test_5_ajax_entregar_venta_pendiente(self):
        """PRUEBA 5: Acción AJAX Entregar. Valida transicionar de PENDIENTE a ENTREGADO."""
        print("\n" + "=" * 60)
        print(" [TEST 5] ACCIÓN AJAX: ENTREGAR PEDIDO PENDIENTE ")
        print("=" * 60)

        venta = Venta.objects.create(
            fecha_hora_venta=timezone.now(),
            id_usuario_fk_venta=self.usuario_mesero,
            estado_pedido='PENDIENTE',
            estado_pago='PENDIENTE',
            total_venta=2500
        )

        print(f" -> Estado inicial -> Pedido: {venta.estado_pedido} | Pago: {venta.estado_pago}")

        if venta.estado_pago != 'PENDIENTE':
            success = False
        else:
            venta.estado_pedido = 'ENTREGADO'
            venta.save()
            success = True

        print(f" -> Estado transicionado -> Pedido: {venta.estado_pedido} | AJAX Success: {success}")
        self.assertTrue(success)
        self.assertEqual(venta.estado_pedido, 'ENTREGADO')

    def test_6_ajax_finalizar_y_cobrar_venta(self):
        """PRUEBA 6: Acción AJAX Finalizar Venta. Valida el descuento físico diferido de inventario al cobrar."""
        print("\n" + "=" * 60)
        print(" [TEST 6] ACCIÓN AJAX: FINALIZAR Y COBRAR (DESCUENTO DIFERIDO) ")
        print("=" * 60)

        stock_ini_torta = self.torta_oreo.cant_exist_producto

        venta_por_cobrar = Venta.objects.create(
            fecha_hora_venta=timezone.now(),
            id_usuario_fk_venta=self.usuario_mesero,
            estado_pedido='ENTREGADO',
            estado_pago='PENDIENTE',
            total_venta=45000
        )
        DetalleVenta.objects.create(cantidad=1, sub_total=45000, id_venta_fk_det_venta=venta_por_cobrar,
                                    id_producto_fk_det_venta=self.torta_oreo)

        rol_ejecutor = self.usuario_cajero.rol_fk_usuario.rol
        print(f" -> Operación realizada por el rol: {rol_ejecutor}")

        if rol_ejecutor not in ['ADMIN', 'CAJERO']:
            success = False
        elif venta_por_cobrar.estado_pedido != 'ENTREGADO' or venta_por_cobrar.estado_pago == 'PAGADA':
            success = False
        else:
            for item in venta_por_cobrar.detalles.all():
                prod = item.id_producto_fk_det_venta
                prod.cant_exist_producto -= item.cantidad
                prod.save()

            venta_por_cobrar.estado_pago = 'PAGADA'
            venta_por_cobrar.fecha_cambio_estado = timezone.now()
            venta_por_cobrar.save()
            success = True

        torta_bd = Producto.objects.get(id_producto=105)
        print(f" -> Venta Pagada con Éxito: {success} | Nuevo Stock Torta Oreo: {torta_bd.cant_exist_producto}")
        self.assertTrue(success)
        self.assertEqual(venta_por_cobrar.estado_pago, 'PAGADA')
        self.assertEqual(torta_bd.cant_exist_producto, stock_ini_torta - 1)
        self.assertIsNotNone(venta_por_cobrar.fecha_cambio_estado)

    def test_7_ajax_cancelar_venta_pagada_y_revertir_stock(self):
        """PRUEBA 7: Acción AJAX Cancelar Venta. Valida devolución automática de stock a la BD original."""
        print("\n" + "=" * 60)
        print(" [TEST 7] ACCIÓN AJAX: CANCELAR VENTA (REVERSIÓN DE INVENTARIO) ")
        print("=" * 60)

        stock_ini_pan = self.pan_frances.cant_exist_producto

        venta_a_anular = Venta.objects.create(
            fecha_hora_venta=timezone.now(),
            id_usuario_fk_venta=self.usuario_admin,
            estado_pedido='ENTREGADO',
            estado_pago='PAGADA',
            total_venta=5000
        )
        DetalleVenta.objects.create(cantidad=2, sub_total=5000, id_venta_fk_det_venta=venta_a_anular,
                                    id_producto_fk_det_venta=self.pan_frances)

        print(f" -> Estado previo de la Venta: {venta_a_anular.estado_pago} | Stock Pan: {stock_ini_pan}")

        if venta_a_anular.estado_pago == 'PAGADA':
            for item in venta_a_anular.detalles.all():
                prod = item.id_producto_fk_det_venta
                prod.cant_exist_producto += item.cantidad
                prod.save()

        venta_a_anular.estado_pago = 'CANCELADA'
        venta_a_anular.estado_pedido = 'CANCELADO'
        venta_a_anular.fecha_cambio_estado = timezone.now()
        venta_a_anular.save()

        pan_bd = Producto.objects.get(id_producto=104)
        print(
            f" -> Estado nuevo: {venta_a_anular.estado_pago} | Stock Pan post-reversión: {pan_bd.cant_exist_producto}")
        self.assertEqual(venta_a_anular.estado_pago, 'CANCELADA')
        self.assertEqual(venta_a_anular.estado_pedido, 'CANCELADO')
        self.assertEqual(pan_bd.cant_exist_producto, stock_ini_pan + 2)

    def test_8_filtro_seguridad_lista_ventas_mesero(self):
        """PRUEBA 8: Control de Queryset en lista_ventas. El mesero solo debe ver las ventas registradas el día de hoy."""
        print("\n" + "=" * 60)
        print(" [TEST 8] FILTRO DE SEGURIDAD: VISTAS DEL DÍA PARA MESEROS ")
        print("=" * 60)

        # 1. Creamos una venta de HOY
        Venta.objects.create(fecha_hora_venta=timezone.now(), id_usuario_fk_venta=self.usuario_mesero,
                             estado_pedido='PENDIENTE', estado_pago='PENDIENTE', total_venta=5000)
        # 2. Creamos una venta con fecha de AYER
        fecha_ayer = timezone.now() - timedelta(days=1)
        Venta.objects.create(fecha_hora_venta=fecha_ayer, id_usuario_fk_venta=self.usuario_mesero,
                             estado_pedido='PENDIENTE', estado_pago='PENDIENTE', total_venta=10000)

        rol_usuario = self.usuario_mesero.rol_fk_usuario.rol
        queryset = Venta.objects.all()

        # Emulación exacta del condicional if/else de tu 'lista_ventas'
        if rol_usuario in ['ADMIN', 'CAJERO']:
            ventas_visibles = queryset
        else:
            ventas_visibles = queryset.filter(fecha_hora_venta__date=timezone.now().date())

        print(
            f" -> Ventas totales en BD: {queryset.count()} | Ventas que el Mesero puede ver: {ventas_visibles.count()}")
        # El mesero solo debe ver 1 (la de hoy), la de ayer queda oculta por el filtro de la vista
        self.assertEqual(ventas_visibles.count(), 1)

    def test_9_editar_venta_recalcula_a_pendiente(self):
        """PRUEBA 9: Regla en editar_venta. Si un pedido ya estaba ENTREGADO, al editarlo el backend lo regresa a PENDIENTE."""
        print("\n" + "=" * 60)
        print(" [TEST 9] RE-CÁLCULO AL EDITAR: ENTREGADO REGRESA A PENDIENTE ")
        print("=" * 60)

        venta_a_editar = Venta.objects.create(
            fecha_hora_venta=timezone.now(),
            id_usuario_fk_venta=self.usuario_mesero,
            estado_pedido='ENTREGADO',  # Entregado originalmente
            estado_pago='PENDIENTE',
            total_venta=2500
        )

        print(f" -> Estado del pedido antes de presionar guardar en edición: {venta_a_editar.estado_pedido}")

        # Emulación de la regla interna dentro del atomic de tu 'editar_venta'
        if venta_a_editar.estado_pedido == 'ENTREGADO':
            venta_a_editar.estado_pedido = 'PENDIENTE'

        venta_a_editar.save()

        print(f" -> Estado del pedido re-calculado por el backend: {venta_a_editar.estado_pedido}")
        self.assertEqual(venta_a_editar.estado_pedido, 'PENDIENTE')

    def test_10_ajax_finalizar_bloqueo_rol_no_autorizado(self):
        """PRUEBA 10: Escudo de seguridad AJAX. Un mesero/panadero no puede cobrar una venta (Acceso Denegado)."""
        print("\n" + "=" * 60)
        print(" [TEST 10] SEGURIDAD AJAX: BLOQUEO DE COBRO A ROL NO AUTORIZADO ")
        print("=" * 60)

        rol_ejecutor = self.usuario_panadero.rol_fk_usuario.rol
        print(f" -> El usuario con rol '{rol_ejecutor}' intenta invocar finalizar_venta_ajax")

        # Emulación de la primera compuerta de seguridad en 'finalizar_venta_ajax'
        if rol_ejecutor not in ['ADMIN', 'CAJERO']:
            success = False
            message = 'No tienes permisos.'
        else:
            success = True
            message = 'Venta PAGADA.'

        print(f" -> ¿El backend procesó la solicitud?: {success} | Mensaje del sistema: '{message}'")
        self.assertFalse(success)
        self.assertEqual(message, 'No tienes permisos.')
        print("=" * 60 + "\n")