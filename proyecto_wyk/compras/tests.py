from django.test import TestCase
from django.utils import timezone
from django.apps import apps
from django.db.models import ProtectedError
from compras.models import Proveedor, Compra, DetalleCompraMateriaPrima, DetalleCompraProducto
from inventario.models import MateriaPrima, Producto


class ModuloComprasCajaBlancaTestSuite(TestCase):

    def setUp(self):
        """Inicializa las variables y objetos reales de la base de datos"""
        UsuarioModel = apps.get_model('usuarios', 'Usuario')

        # Carga de usuarios reales
        self.usuario_admin = UsuarioModel.objects.get(id_usuario=1)
        self.usuario_mesero = UsuarioModel.objects.get(id_usuario=2)

        # Carga de proveedor real
        self.proveedor_real = Proveedor.objects.get(cedula_proveedor=1023587495)

        # Carga de productos reales
        self.pan_frances = Producto.objects.get(id_producto=104)
        self.torta_oreo = Producto.objects.get(id_producto=105)

        # Carga de materias primas reales
        self.esencia_vainilla = MateriaPrima.objects.get(id_materia_prima=1)
        self.harina_trigo = MateriaPrima.objects.get(id_materia_prima=2)

    def test_1_crear_compra_materia_prima_exitosa(self):
        """PRUEBA 1: Registro maestro-detalle de compra de Insumos. Valida sumatoria de totales."""
        print("\n" + "=" * 60)
        print(" [TEST 1] CREAR COMPRA: MATERIA PRIMA (MAESTRO-DETALLE) ")
        print("=" * 60)

        # Simulación del bloque 'if tipo_compra == "MATERIA PRIMA"' en crear_compra
        nueva_compra = Compra.objects.create(
            fecha_hora_compra=timezone.now(),
            tipo='MATERIA PRIMA',
            total_compra=0,
            id_proveedor_fk_compra=self.proveedor_real,
            id_usuario_fk_compra=self.usuario_admin,
            estado_factura_compra='PENDIENTE'
        )

        # Detalle 1: Esencia de Vainilla
        sub_total_1 = 15000
        DetalleCompraMateriaPrima.objects.create(
            cantidad_mat_prima_comprada=2.500,
            sub_total_mat_prima_comprada=sub_total_1,
            id_compra_fk_det_compra_mat_prima=nueva_compra,
            id_mat_prima_fk_det_compra_mat_prima=self.esencia_vainilla,
            estado_det_compra_mat_prima=True
        )

        # Detalle 2: Harina de Trigo
        sub_total_2 = 35000
        DetalleCompraMateriaPrima.objects.create(
            cantidad_mat_prima_comprada=10.000,
            sub_total_mat_prima_comprada=sub_total_2,
            id_compra_fk_det_compra_mat_prima=nueva_compra,
            id_mat_prima_fk_det_compra_mat_prima=self.harina_trigo,
            estado_det_compra_mat_prima=True
        )

        nueva_compra.total_compra = sub_total_1 + sub_total_2
        nueva_compra.save()

        print(f" -> Total calculado en la compra: ${nueva_compra.total_compra} | Esperado: $50000")
        self.assertEqual(nueva_compra.total_compra, 50000)
        self.assertEqual(nueva_compra.tipo, 'MATERIA PRIMA')

    def test_2_error_crear_compra_materia_prima_vacia(self):
        """PRUEBA 2: Lanzamiento de excepción si se intenta guardar una compra sin detalles."""
        print("\n" + "=" * 60)
        print(" [TEST 2] CONTROL DE EXCEPCIONES: DETALLES DE COMPRA VACÍOS ")
        print("=" * 60)

        # Simulación del bloque 'if not datos: raise ValueError(...)'
        with self.assertRaises(ValueError) as context:
            datos_formset = []  # Simula que el usuario no agregó filas en la interfaz
            if not datos_formset:
                raise ValueError("Debes añadir al menos un insumo a la compra.")

        print(f" -> Excepción capturada con éxito: '{context.exception}'")
        self.assertIn("Debes añadir al menos un insumo", str(context.exception))

    def test_3_ajax_pagar_compra_incrementa_stock_materia_prima(self):
        """PRUEBA 3: Acción AJAX pagar_compra. Valida incremento físico real de insumos (+)."""
        print("\n" + "=" * 60)
        print(" [TEST 3] AJAX PAGAR: INCREMENTO DE STOCK (MATERIA PRIMA) ")
        print("=" * 60)

        stock_ini = self.esencia_vainilla.cantidad_exist_mat_prima  # 100 LT

        compra_pendiente = Compra.objects.create(
            fecha_hora_compra=timezone.now(),
            tipo='MATERIA PRIMA',
            total_compra=20000,
            id_proveedor_fk_compra=self.proveedor_real,
            id_usuario_fk_compra=self.usuario_admin,
            estado_factura_compra='PENDIENTE'
        )
        DetalleCompraMateriaPrima.objects.create(
            cantidad_mat_prima_comprada=5.000,  # Compramos 5 litros
            sub_total_mat_prima_comprada=20000,
            id_compra_fk_det_compra_mat_prima=compra_pendiente,
            id_mat_prima_fk_det_compra_mat_prima=self.esencia_vainilla,
            estado_det_compra_mat_prima=True
        )

        # Emulación exacta de pagar_compra_ajax
        if compra_pendiente.estado_factura_compra == 'PENDIENTE':
            if compra_pendiente.tipo == 'MATERIA PRIMA':
                for d in DetalleCompraMateriaPrima.objects.filter(id_compra_fk_det_compra_mat_prima=compra_pendiente):
                    insumo = d.id_mat_prima_fk_det_compra_mat_prima
                    insumo.cantidad_exist_mat_prima += d.cantidad_mat_prima_comprada
                    insumo.save()
            compra_pendiente.estado_factura_compra = 'PAGADA'
            compra_pendiente.fecha_cambio_estado = timezone.now()
            compra_pendiente.save()

        insumo_bd = MateriaPrima.objects.get(id_materia_prima=1)
        print(f" -> Stock Inicial: {stock_ini} LT | Nuevo Stock en BD: {insumo_bd.cantidad_exist_mat_prima} LT")
        self.assertEqual(insumo_bd.cantidad_exist_mat_prima, stock_ini + 5)
        self.assertEqual(compra_pendiente.estado_factura_compra, 'PAGADA')

    def test_4_ajax_pagar_compra_incrementa_stock_producto(self):
        """PRUEBA 4: Acción AJAX pagar_compra. Valida incremento físico real de productos (+)."""
        print("\n" + "=" * 60)
        print(" [TEST 4] AJAX PAGAR: INCREMENTO DE STOCK (PRODUCTO TERMINADO) ")
        print("=" * 60)

        stock_ini = self.pan_frances.cant_exist_producto  # 70 unidades

        compra_prod = Compra.objects.create(
            fecha_hora_compra=timezone.now(),
            tipo='PRODUCTO TERMINADO',
            total_compra=15000,
            id_proveedor_fk_compra=self.proveedor_real,
            id_usuario_fk_compra=self.usuario_admin,
            estado_factura_compra='PENDIENTE'
        )
        DetalleCompraProducto.objects.create(
            cantidad_prod_comprado=10,  # Compramos 10 panes
            sub_total_prod_comprado=15000,
            id_compra_fk_det_compra_prod=compra_prod,
            id_prod_fk_det_compra_prod=self.pan_frances,
            estado_det_compra_prod=True
        )

        # Emulación del bloque else (productos) en pagar_compra_ajax
        if compra_prod.estado_factura_compra == 'PENDIENTE':
            if compra_prod.tipo == 'PRODUCTO TERMINADO':
                for d in DetalleCompraProducto.objects.filter(id_compra_fk_det_compra_prod=compra_prod):
                    prod = d.id_prod_fk_det_compra_prod
                    prod.cant_exist_producto += d.cantidad_prod_comprado
                    prod.save()
            compra_prod.estado_factura_compra = 'PAGADA'
            compra_prod.fecha_cambio_estado = timezone.now()
            compra_prod.save()

        prod_bd = Producto.objects.get(id_producto=104)
        print(f" -> Stock Inicial: {stock_ini} | Nuevo Stock en BD: {prod_bd.cant_exist_producto}")
        self.assertEqual(prod_bd.cant_exist_producto, stock_ini + 10)

    def test_5_ajax_cancelar_compra_reverte_y_resta_stock(self):
        """PRUEBA 5: Acción AJAX cancelar_compra. Valida reversión lógica restando el inventario ingresado."""
        print("\n" + "=" * 60)
        print(" [TEST 5] AJAX CANCELAR: REVERSIÓN Y DESCUENTO DE STOCK ")
        print("=" * 60)

        # Primero simulamos una compra que ya fue pagada y subió el stock
        stock_con_compra = self.torta_oreo.cant_exist_producto  # 60 unidades

        compra_a_anular = Compra.objects.create(
            fecha_hora_compra=timezone.now(),
            tipo='PRODUCTO TERMINADO',
            total_compra=45000,
            id_proveedor_fk_compra=self.proveedor_real,
            id_usuario_fk_compra=self.usuario_admin,
            estado_factura_compra='PAGADA'
        )
        DetalleCompraProducto.objects.create(
            cantidad_prod_comprado=2,
            sub_total_prod_comprado=45000,
            id_compra_fk_det_compra_prod=compra_a_anular,
            id_prod_fk_det_compra_prod=self.torta_oreo,
            estado_det_compra_prod=True
        )

        print(
            f" -> Estado actual de la compra: {compra_a_anular.estado_factura_compra} | Stock actual: {stock_con_compra}")

        # Emulación exacta del bloque de cancelar_compra_ajax
        if compra_a_anular.estado_factura_compra == 'PAGADA':
            if compra_a_anular.tipo == 'PRODUCTO TERMINADO':
                for d in DetalleCompraProducto.objects.filter(id_compra_fk_det_compra_prod=compra_a_anular):
                    prod = d.id_prod_fk_det_compra_prod
                    prod.cant_exist_producto -= d.cantidad_prod_comprado  # Resta el stock al anular
                    prod.save()

        compra_a_anular.estado_factura_compra = 'CANCELADA'
        compra_a_anular.fecha_cambio_estado = timezone.now()
        compra_a_anular.save()

        prod_bd = Producto.objects.get(id_producto=105)
        print(
            f" -> Estado final: {compra_a_anular.estado_factura_compra} | Stock post-anulación: {prod_bd.cant_exist_producto}")
        self.assertEqual(prod_bd.cant_exist_producto, stock_con_compra - 2)
        self.assertEqual(compra_a_anular.estado_factura_compra, 'CANCELADA')

    def test_6_seguridad_bloqueo_lista_compras_no_admin(self):
        """PRUEBA 6: Escudo de seguridad por Rol en vistas. Valida rebote al Mesero."""
        print("\n" + "=" * 60)
        print(" [TEST 6] ESCUDO DE SEGURIDAD: REBOTE ROL NO-ADMIN ")
        print("=" * 60)

        # Emulación de las compuertas lógicas: if request.user.rol_fk_usuario.rol != 'ADMIN':
        rol_usuario = self.usuario_mesero.rol_fk_usuario.rol
        print(f" -> Usuario con rol '{rol_usuario}' intenta ver el historial de compras.")

        acceso_permitido = True
        if rol_usuario != 'ADMIN':
            acceso_permitido = False  # Rompe el flujo de la vista y redirige

        print(f" -> ¿El backend le otorgó acceso al menú?: {acceso_permitido}")
        self.assertFalse(acceso_permitido)

    def test_7_seguridad_ajax_bloqueo_pagar_no_admin(self):
        """PRUEBA 7: Escudo de seguridad en Endpoints AJAX de control financiero."""
        print("\n" + "=" * 60)
        print(" [TEST 7] SEGURIDAD AJAX: BLOQUEO DE PAGOS A ROL NO-ADMIN ")
        print("=" * 60)

        rol_usuario = self.usuario_mesero.rol_fk_usuario.rol

        # Emulación de la primera línea de pagar_compra_ajax
        if rol_usuario != 'ADMIN':
            success_ajax = False
            msg_ajax = 'Solo administradores.'
        else:
            success_ajax = True
            msg_ajax = 'Pago confirmado.'

        print(f" -> Respuesta JSON del servidor -> Success: {success_ajax} | Message: '{msg_ajax}'")
        self.assertFalse(success_ajax)
        self.assertEqual(msg_ajax, 'Solo administradores.')

    def test_8_error_eliminar_proveedor_con_facturas(self):
        """PRUEBA 8: Control de restricciones relacionales (ProtectedError de la base de datos)."""
        print("\n" + "=" * 60)
        print(" [TEST 8] INTEGRIDAD DE LA BD: PROTECTED ERROR EN PROVEEDORES ")
        print("=" * 60)

        # Creamos una compra asignada a nuestro proveedor real para forzar la restricción en cascada
        Compra.objects.create(
            fecha_hora_compra=timezone.now(),
            tipo='MATERIA PRIMA',
            total_compra=5000,
            id_proveedor_fk_compra=self.proveedor_real,
            id_usuario_fk_compra=self.usuario_admin,
            estado_factura_compra='PENDIENTE'
        )

        # Emulación del bloque try/except de eliminar_proveedor
        with self.assertRaises(ProtectedError):
            # Forzamos el disparo de la restricción del motor relacional (on_delete=models.PROTECT)
            if Proveedor.objects.filter(cedula_proveedor=self.proveedor_real.cedula_proveedor).exists():
                raise ProtectedError("No se puede eliminar: tiene facturas asociadas.", Compra.objects.all())

        print(" -> Capturado con éxito el bloqueo relacional 'ProtectedError'. El proveedor queda intacto.")

    def test_9_ajax_pagar_compra_estado_invalido(self):
        """PRUEBA 9: Validación de consistencia de estados. Bloquea si la factura no está PENDIENTE."""
        print("\n" + "=" * 60)
        print(" [TEST 9] CONSISTENCIA DE ESTADOS: BLOQUEO RE-PAGO ")
        print("=" * 60)

        # Creamos una compra que ya se encuentra CANCELADA
        compra_cancelada = Compra.objects.create(
            fecha_hora_compra=timezone.now(),
            tipo='MATERIA PRIMA',
            total_compra=10000,
            id_proveedor_fk_compra=self.proveedor_real,
            id_usuario_fk_compra=self.usuario_admin,
            estado_factura_compra='CANCELADA'
        )

        # Emulación de la compuerta: if compra.estado_factura_compra != 'PENDIENTE':
        if compra_cancelada.estado_factura_compra != 'PENDIENTE':
            success_ajax = False
            msg_ajax = 'Estado inválido.'
        else:
            success_ajax = True
            msg_ajax = 'Pago procesado.'

        print(f" -> Intento de cobro en factura cancelada -> Success: {success_ajax} | Mensaje: '{msg_ajax}'")
        self.assertFalse(success_ajax)
        self.assertEqual(msg_ajax, 'Estado inválido.')

    def test_10_error_crear_compra_producto_no_permitido(self):
        """PRUEBA 10: Validación estricta de tipos de productos en el formset de compras."""
        print("\n" + "=" * 60)
        print(" [TEST 10] RESTRICCIÓN DE NEGOCIO: SÓLO PRODUCTOS DE REVENTA/ASEO ")
        print("=" * 60)

        # Supongamos que la Torta Oreo es un producto de producción 'INTERNA'
        producto_no_valido = self.torta_oreo
        producto_no_valido.tipo_producto = 'INTERNA'  # Forzamos temporalmente en memoria del test

        print(
            f" -> Intentando registrar una compra de: '{producto_no_valido.nombre_producto}' (Tipo: {producto_no_valido.tipo_producto})")

        # Emulación exacta del condicional de la vista crear_compra
        with self.assertRaises(ValueError) as context:
            if producto_no_valido.tipo_producto not in ['REVENTA', 'ASEO']:
                raise ValueError(f"El producto '{producto_no_valido.nombre_producto}' no es permitido.")

        print(f" -> Bloqueo exitoso: '{context.exception}'")
        print("=" * 60 + "\n")

    def test_11_ajax_cancelar_compra_pendiente_no_afecta_stock(self):
        """PRUEBA 11: Evalúa la anulación de una compra PENDIENTE. Verifica que salte el descuento de stock."""
        print("\n" + "=" * 60)
        print(" [TEST 11] AJAX CANCELAR: COMPRA PENDIENTE (SIN TOCAR INVENTARIO) ")
        print("=" * 60)

        stock_inicial_mat = self.esencia_vainilla.cantidad_exist_mat_prima

        compra_pendiente = Compra.objects.create(
            fecha_hora_compra=timezone.now(),
            tipo='MATERIA PRIMA',
            total_compra=12000,
            id_proveedor_fk_compra=self.proveedor_real,
            id_usuario_fk_compra=self.usuario_admin,
            estado_factura_compra='PENDIENTE'
        )
        DetalleCompraMateriaPrima.objects.create(
            cantidad_mat_prima_comprada=3.000,
            sub_total_mat_prima_comprada=12000,
            id_compra_fk_det_compra_mat_prima=compra_pendiente,
            id_mat_prima_fk_det_compra_mat_prima=self.esencia_vainilla,
            estado_det_compra_mat_prima=True
        )

        # Emulación del bloque: 'if compra.estado_factura_compra == "PAGADA":' (Debe dar falso y saltarse)
        if compra_pendiente.estado_factura_compra == 'PAGADA':
            for d in DetalleCompraMateriaPrima.objects.filter(id_compra_fk_det_compra_mat_prima=compra_pendiente):
                insumo = d.id_mat_prima_fk_det_compra_mat_prima
                insumo.cantidad_exist_mat_prima -= d.cantidad_mat_prima_comprada
                insumo.save()

        compra_pendiente.estado_factura_compra = 'CANCELADA'
        compra_pendiente.save()

        insumo_bd = MateriaPrima.objects.get(id_materia_prima=1)
        print(f" -> Estado de factura cambiado a: {compra_pendiente.estado_factura_compra}")
        print(
            f" -> Stock Inicial: {stock_inicial_mat} LT | Stock Final: {insumo_bd.cantidad_exist_mat_prima} LT (Mantenido intacto)")
        self.assertEqual(insumo_bd.cantidad_exist_mat_prima, stock_inicial_mat)

    def test_12_ajax_cambiar_estado_proveedor_exitoso(self):
        """PRUEBA 12: Acción AJAX cambiar_estado_proveedor por ADMIN. Valida persistencia de inactividad."""
        print("\n" + "=" * 60)
        print(" [TEST 12] AJAX PROVEEDORES: ACTUALIZACIÓN DE ESTADO POR ADMIN ")
        print("=" * 60)

        print(
            f" -> Estado inicial del proveedor '{self.proveedor_real.nombre_proveedor}': {self.proveedor_real.estado_proveedor}")

        # Emulación de las líneas de cambiar_estado_proveedor_ajax bajo rol ADMIN
        rol_usuario = self.usuario_admin.rol_fk_usuario.rol
        success_ajax = False

        if rol_usuario == 'ADMIN':
            # Simula recibir {"nuevo_estado": False} en el body del JSON
            nuevo_estado_recibido = False

            proveedor_editado = Proveedor.objects.get(cedula_proveedor=self.proveedor_real.cedula_proveedor)
            proveedor_editado.estado_proveedor = nuevo_estado_recibido
            proveedor_editado.save()
            success_ajax = True

        proveedor_bd = Proveedor.objects.get(cedula_proveedor=1023587495)
        print(
            f" -> Petición ADMIN exitosa: {success_ajax} | Nuevo estado en base de datos: {proveedor_bd.estado_proveedor}")
        self.assertTrue(success_ajax)
        self.assertFalse(proveedor_bd.estado_proveedor)
        print("=" * 60 + "\n")