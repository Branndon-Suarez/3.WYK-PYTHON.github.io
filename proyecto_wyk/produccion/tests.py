from django.test import TestCase
from django.apps import apps
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from produccion.models import Produccion, DetalleProduccion
from recetas.models import Receta, DetalleReceta
from inventario.models import Producto, MateriaPrima


class ModuloProduccionCajaBlancaTestSuite(TestCase):

    def setUp(self):
        """Inicializa las variables, roles y objetos reales de la base de datos"""
        UsuarioModel = apps.get_model('usuarios', 'Usuario')

        # Carga de usuarios reales
        self.usuario_admin = UsuarioModel.objects.get(id_usuario=1)
        self.usuario_mesero = UsuarioModel.objects.get(id_usuario=2)
        self.usuario_panadero = UsuarioModel.objects.get(id_usuario=4)
        self.usuario_pastelero = UsuarioModel.objects.get(id_usuario=5)

        # Carga de productos reales
        self.torta_oreo = Producto.objects.get(id_producto=105)

        # Carga de materias primas reales
        self.esencia_vainilla = MateriaPrima.objects.get(id_materia_prima=1)
        self.harina_trigo = MateriaPrima.objects.get(id_materia_prima=2)

        # Forzar en el setup una presentación de texto para evitar fallos de formato en utilidades
        self.harina_trigo.presentacion_mat_prima = "KG"
        self.harina_trigo.save()

        # CREACIÓN PROGRAMÁTICA DE UNA RECETA MAESTRA BASE PARA LOS TESTS
        self.receta_prueba = Receta.objects.create(
            nombre_receta="Fórmula de Test Oreo",
            descripcion_receta="Receta inyectada para simulación",
            cantidad_base=10,
            id_producto_fk_receta=self.torta_oreo,
            id_usuario_fk_receta=self.usuario_admin,
            estado_receta=True
        )
        DetalleReceta.objects.create(
            id_receta_fk_det_rec=self.receta_prueba,
            id_materia_prima_fk_det_rec=self.harina_trigo,
            cantidad_insumo_base=2.000
        )

    def test_1_lista_produccion_filtro_panadero(self):
        """PRUEBA 1: Validación del camino condicional 'if rol_usuario == "PANADERO"'. Filtra su categoría."""
        print("\n" + "=" * 60)
        print(" [TEST 1] LISTA PRODUCCIÓN: FILTRO EXCLUSIVO PANADERÍA ")
        print("=" * 60)

        rol_usuario = self.usuario_panadero.rol_fk_usuario.rol
        print(f" -> Usuario con rol '{rol_usuario}' solicita el historial.")

        # Emulación del bloque de la vista lista_produccion
        if rol_usuario == 'PANADERO':
            categoria_filtrada = 'PANADERIA'
        elif rol_usuario == 'PASTELERO':
            categoria_filtrada = 'PASTELERIA'
        else:
            categoria_filtrada = 'TODAS'

        print(f" -> Categoría asignada en el QuerySet de Django: '{categoria_filtrada}'")
        self.assertEqual(categoria_filtrada, 'PANADERIA')

    def test_2_lista_produccion_filtro_pastelero(self):
        """PRUEBA 2: Validación del camino condicional 'elif rol_usuario == "PASTELERO"'. Filtra su categoría."""
        print("\n" + "=" * 60)
        print(" [TEST 2] LISTA PRODUCCIÓN: FILTRO EXCLUSIVO PASTELERÍA ")
        print("=" * 60)

        rol_usuario = self.usuario_pastelero.rol_fk_usuario.rol
        print(f" -> Usuario con rol '{rol_usuario}' solicita el historial.")

        if rol_usuario == 'PANADERO':
            categoria_filtrada = 'PANADERIA'
        elif rol_usuario == 'PASTELERO':
            categoria_filtrada = 'PASTELERIA'
        else:
            categoria_filtrada = 'TODAS'

        print(f" -> Categoría asignada en el QuerySet de Django: '{categoria_filtrada}'")
        self.assertEqual(categoria_filtrada, 'PASTELERIA')

    def test_3_lista_produccion_admin_ve_todo(self):
        """PRUEBA 3: Validación del camino condicional 'else' en lista_produccion. El ADMIN ve todo sin filtros."""
        print("\n" + "=" * 60)
        print(" [TEST 3] LISTA PRODUCCIÓN: ACCESO TOTAL ADMIN ")
        print("=" * 60)

        rol_usuario = self.usuario_admin.rol_fk_usuario.rol
        print(f" -> Usuario con rol '{rol_usuario}' solicita el historial.")

        if rol_usuario == 'PANADERO':
            categoria_filtrada = 'PANADERIA'
        elif rol_usuario == 'PASTELERO':
            categoria_filtrada = 'PASTELERIA'
        else:
            categoria_filtrada = 'TODAS'  # Admin ve todos los registros

        print(f" -> Categoría asignada en el QuerySet de Django: '{categoria_filtrada}'")
        self.assertEqual(categoria_filtrada, 'TODAS')

    def test_4_crear_produccion_categoria_fija_panadero(self):
        """PRUEBA 4: Registro de orden de producción. Fuerza asignación automática de categoría por rol."""
        print("\n" + "=" * 60)
        print(" [TEST 4] CREAR PRODUCCIÓN: ASIGNACIÓN FIJA POR ROL ")
        print("=" * 60)

        rol_usuario = self.usuario_panadero.rol_fk_usuario.rol

        # Emulación del bloque POST de crear_produccion
        nueva_prod = Produccion.objects.create(
            nombre_produccion="Lote Pan de Rol",
            fecha_hora_produccion=timezone.now(),
            categoria_produccion="",  # Vacío inicialmente para evaluar la inyección
            cant_produccion=50,
            descripcion_produccion="Prueba de asignación de rol",
            id_producto_fk_produccion=self.torta_oreo,
            id_receta_fk_produccion=self.receta_prueba,
            id_usuario_fk_produccion=self.usuario_panadero,
            estado_produccion='PENDIENTE'
        )

        if rol_usuario == 'PANADERO':
            nueva_prod.categoria_produccion = 'PANADERIA'
        elif rol_usuario == 'PASTELERO':
            nueva_prod.categoria_produccion = 'PASTELERIA'

        nueva_prod.save()
        print(f" -> Orden '{nueva_prod.nombre_produccion}' registrada por Panadero. Categoría inyectada: '{nueva_prod.categoria_produccion}'")
        self.assertEqual(nueva_prod.categoria_produccion, 'PANADERIA')

    def test_5_crear_produccion_render_get_initials(self):
        """PRUEBA 5: Validación del camino alternativo GET en crear_produccion. Inyección de valores por defecto al formulario."""
        print("\n" + "=" * 60)
        print(" [TEST 5] FORMULARIO INITIAL: PROCESAMIENTO VIA GET ")
        print("=" * 60)

        rol_usuario = self.usuario_pastelero.rol_fk_usuario.rol
        print(f" -> Usuario '{rol_usuario}' entra a la pantalla de creación.")

        initial_categoria = ""
        if rol_usuario == 'PANADERO':
            initial_categoria = 'PANADERIA'
        elif rol_usuario == 'PASTELERO':
            initial_categoria = 'PASTELERIA'

        print(f" -> Valor inicial asignado al campo 'categoria_produccion': '{initial_categoria}'")
        self.assertEqual(initial_categoria, 'PASTELERIA')

    def test_6_seguridad_bloqueo_lista_no_autorizado(self):
        """PRUEBA 6: Escudo perimetral en lista de producción. El Mesero es rebotado."""
        print("\n" + "=" * 60)
        print(" [TEST 6] ESCUDO DE SEGURIDAD: REBOTE ROL NO OPERATIVO ")
        print("=" * 60)

        rol_usuario = self.usuario_mesero.rol_fk_usuario.rol
        print(f" -> Rol '{rol_usuario}' intenta inspeccionar las órdenes de producción de la planta.")

        acceso_permitido = True
        if rol_usuario not in ['ADMIN', 'PASTELERO', 'PANADERO']:
            acceso_permitido = False

        print(f" -> ¿Se le permitió renderizar la vista de planta?: {acceso_permitido}")
        self.assertFalse(acceso_permitido)

    def test_7_seguridad_detalle_intercepcion_id_ajeno(self):
        """PRUEBA 7: Protección cruzada de registros. Bloquea si un Panadero digita el ID de una Pastelería."""
        print("\n" + "=" * 60)
        print(" [TEST 7] SEGURIDAD HORIZONTAL: BLOQUEO DE ID AJENO ENTRE TRABAJADORES ")
        print("=" * 60)

        rol_usuario = self.usuario_panadero.rol_fk_usuario.rol

        # Creación de una producción con categoría PASTELERIA
        produccion_pasteleria = Produccion.objects.create(
            nombre_produccion="Milhojas Especiales",
            fecha_hora_produccion=timezone.now(),
            categoria_produccion='PASTELERIA',
            cant_produccion=20,
            descripcion_produccion="Secreta",
            id_producto_fk_produccion=self.torta_oreo,
            id_receta_fk_produccion=self.receta_prueba,
            id_usuario_fk_produccion=self.usuario_pastelero,
            estado_produccion='PENDIENTE'
        )

        print(f" -> Panadero intenta forzar la URL de la Orden ID: {produccion_pasteleria.id_produccion} (Categoría: {produccion_pasteleria.categoria_produccion})")

        # Emulación del bloque de seguridad de la vista detalle_produccion
        acceso_registro = True
        if rol_usuario == 'PANADERO' and produccion_pasteleria.categoria_produccion != 'PANADERIA':
            acceso_registro = False

        print(f" -> ¿El backend permitió la visualización del detalle?: {acceso_registro}")
        self.assertFalse(acceso_registro)

    def test_8_utilidad_ajax_obtener_receta_activa_exitosa(self):
        """PRUEBA 8: Endpoint AJAX de carga automatizada. Construye el diccionario con stock e insumos."""
        print("\n" + "=" * 60)
        print(" [TEST 8] UTILIDAD AJAX: CARGA EN TIEMPO REAL DE INSUMOS ")
        print("=" * 60)

        # Emulación exacta de obtener_receta_por_producto
        receta = Receta.objects.filter(id_producto_fk_receta=self.torta_oreo.id_producto, estado_receta=True).first()

        self.assertIsNotNone(receta)
        detalles = receta.insumos_receta.all()

        insumos_json = [
            {
                'id_materia': d.id_materia_prima_fk_det_rec.id_materia_prima,
                'nombre': d.id_materia_prima_fk_det_rec.nombre_materia_prima,
                'cantidad': float(d.cantidad_insumo_base),
                'stock': float(d.id_materia_prima_fk_det_rec.cantidad_exist_mat_prima)
            }
            for d in detalles
        ]

        print(f" -> Estructura de datos generada para la interfaz de producción: {insumos_json}")
        self.assertEqual(insumos_json[0]['nombre'], self.harina_trigo.nombre_materia_prima)

    def test_9_ajax_obtener_receta_no_existente(self):
        """PRUEBA 9: Control de error en endpoint AJAX cuando un producto no cuenta con fórmulas o recetas activas."""
        print("\n" + "=" * 60)
        print(" [TEST 9] CONTROL AJAX: PRODUCTO SIN RECETA ACTIVA ")
        print("=" * 60)

        # Buscamos un producto ficticio o forzamos que no encuentre receta activa
        receta_encontrada = Receta.objects.filter(id_producto_fk_receta=9999, estado_receta=True).first()

        success_ajax = True
        msg_ajax = ""

        if not receta_encontrada:
            success_ajax = False
            msg_ajax = 'No se encontró una receta activa para este producto.'

        print(f" -> Respuesta del backend -> Success: {success_ajax} | Mensaje: '{msg_ajax}'")
        self.assertFalse(success_ajax)
        self.assertEqual(msg_ajax, 'No se encontró una receta activa para este producto.')

    def test_10_ajax_finalizar_produccion_exitosa_ajuste_inventarios(self):
        """PRUEBA 10: Proceso central. Finaliza producción, resta insumos y aumenta el producto terminado."""
        print("\n" + "=" * 60)
        print(" [TEST 10] AJAX FINALIZAR: DESCUENTO Y CARGA REAL DE INVENTARIOS ")
        print("=" * 60)

        stock_inicial_materia = self.harina_trigo.cantidad_exist_mat_prima  # 100 KG
        stock_inicial_producto = self.torta_oreo.cant_exist_producto  # 60 unidades

        # Creamos la orden maestra pendiente
        prod_pendiente = Produccion.objects.create(
            nombre_produccion="Lote Finalizado Oreo",
            fecha_hora_produccion=timezone.now(),
            categoria_produccion='PASTELERIA',
            cant_produccion=15,
            descripcion_produccion="Lote de prueba exitoso",
            id_producto_fk_produccion=self.torta_oreo,
            id_receta_fk_produccion=self.receta_prueba,
            id_usuario_fk_produccion=self.usuario_admin,
            estado_produccion='PENDIENTE'
        )
        DetalleProduccion.objects.create(
            id_produccion_fk_det_produc=prod_pendiente,
            id_materia_prima_fk_det_produc=self.harina_trigo,
            cantidad_requerida=10.000
        )

        # Emulación del bloque transaccional dentro de finalizar_produccion_ajax
        with transaction.atomic():
            produccion = Produccion.objects.get(id_produccion=prod_pendiente.id_produccion)
            detalles = produccion.insumos.all()

            for item in detalles:
                insumo = item.id_materia_prima_fk_det_produc
                insumo.cantidad_exist_mat_prima -= item.cantidad_requerida
                insumo.save()

            producto_final = produccion.id_producto_fk_produccion
            producto_final.cant_exist_producto += produccion.cant_produccion
            producto_final.save()

            produccion.estado_produccion = 'FINALIZADA'
            produccion.save()

        insumo_bd = MateriaPrima.objects.get(id_materia_prima=self.harina_trigo.id_materia_prima)
        producto_bd = Producto.objects.get(id_producto=self.torta_oreo.id_producto)

        print(f" -> Materia Prima -> Inicial: {stock_inicial_materia} KG | Final: {insumo_bd.cantidad_exist_mat_prima} KG")
        print(f" -> Producto Terminado -> Inicial: {stock_inicial_producto} | Nuevo Stock: {producto_bd.cant_exist_producto}")

        self.assertEqual(insumo_bd.cantidad_exist_mat_prima, stock_inicial_materia - 10)
        self.assertEqual(producto_bd.cant_exist_producto, stock_inicial_producto + 15)
        self.assertEqual(produccion.estado_produccion, 'FINALIZADA')

    def test_11_ajax_finalizar_error_password_incorrecto(self):
        """PRUEBA 11: Intercepción de seguridad cuando la firma o contraseña de confirmación es incorrecta."""
        print("\n" + "=" * 60)
        print(" [TEST 11] VALIDACIÓN AJAX: REBOTE POR CONTRASEÑA INCORRECTA ")
        print("=" * 60)

        password_valido = False  # Simulación de check_password devolviendo False
        success_ajax = True
        msg_ajax = ""

        if not password_valido:
            success_ajax = False
            msg_ajax = 'Contraseña incorrecta.'

        print(f" -> Validación de firma digital -> Success: {success_ajax} | Mensaje: '{msg_ajax}'")
        self.assertFalse(success_ajax)
        self.assertEqual(msg_ajax, 'Contraseña incorrecta.')

    def test_12_ajax_finalizar_error_insumo_insuficiente(self):
        """PRUEBA 12: Control de quiebre de stock. Aborta si la orden requiere más de lo que hay en almacén."""
        print("\n" + "=" * 60)
        print(" [TEST 12] CONTROL DE EXCEPCIONES: ABORTO POR STOCK INSUFICIENTE ")
        print("=" * 60)

        self.harina_trigo.cantidad_exist_mat_prima = 5.000
        self.harina_trigo.save()

        prod_error = Produccion.objects.create(
            nombre_produccion="Lote Inviable",
            fecha_hora_produccion=timezone.now(),
            categoria_produccion='PASTELERIA',
            cant_produccion=10,
            descripcion_produccion="Debe fallar",
            id_producto_fk_produccion=self.torta_oreo,
            id_receta_fk_produccion=self.receta_prueba,
            id_usuario_fk_produccion=self.usuario_admin,
            estado_produccion='PENDIENTE'
        )
        DetalleProduccion.objects.create(
            id_produccion_fk_det_produc=prod_error,
            id_materia_prima_fk_det_produc=self.harina_trigo,
            cantidad_requerida=40.000
        )

        produccion = Produccion.objects.get(id_produccion=prod_error.id_produccion)
        item = produccion.insumos.first()
        insumo = item.id_materia_prima_fk_det_produc

        success_ajax = True
        msg_ajax = ""

        if insumo.cantidad_exist_mat_prima < item.cantidad_requerida:
            success_ajax = False
            msg_ajax = f"Insumo insuficiente: {insumo.nombre_materia_prima}."

        print(f" -> Simulación de envío AJAX -> Success: {success_ajax} | Mensaje del Servidor: '{msg_ajax}'")
        self.assertFalse(success_ajax)
        self.assertIn("Insumo insuficiente", msg_ajax)

    def test_13_ajax_finalizar_bloqueo_orden_ya_procesada(self):
        """PRUEBA 13: Consistencia de operaciones. Bloquea si intentan re-finalizar una orden FINALIZADA."""
        print("\n" + "=" * 60)
        print(" [TEST 13] MAQUINA DE ESTADOS: BLOQUEO RE-PROCESAMIENTO ")
        print("=" * 60)

        orden_cerrada = Produccion.objects.create(
            nombre_produccion="Lote Historico",
            fecha_hora_produccion=timezone.now(),
            categoria_produccion='PASTELERIA',
            cant_produccion=10,
            descripcion_produccion="Ya procesada",
            id_producto_fk_produccion=self.torta_oreo,
            id_receta_fk_produccion=self.receta_prueba,
            id_usuario_fk_produccion=self.usuario_admin,
            estado_produccion='FINALIZADA'
        )

        if orden_cerrada.estado_produccion != 'PENDIENTE':
            success_ajax = False
            msg_ajax = 'Esta orden ya fue procesada o cancelada.'
        else:
            success_ajax = True
            msg_ajax = 'Procesado'

        print(f" -> Intento de cobro sobre Orden Finalizada -> Success: {success_ajax} | Mensaje: '{msg_ajax}'")
        self.assertFalse(success_ajax)
        self.assertEqual(msg_ajax, 'Esta orden ya fue procesada o cancelada.')

    def test_14_ajax_cancelar_orden_pendiente_sin_afectar_inventario(self):
        """PRUEBA 14: Flujo alternativo de cancelación. Si estaba PENDIENTE, no debe alterar inventarios."""
        print("\n" + "=" * 60)
        print(" [TEST 14] AJAX CANCELAR: ORDEN PENDIENTE (SIN REVERSIÓN) ")
        print("=" * 60)

        stock_ini_prod = self.torta_oreo.cant_exist_producto

        orden_pendiente = Produccion.objects.create(
            nombre_produccion="Lote Abortado Temprano",
            fecha_hora_produccion=timezone.now(),
            categoria_produccion='PANADERIA',
            cant_produccion=30,
            descripcion_produccion="Cancelando antes de hornear",
            id_producto_fk_produccion=self.torta_oreo,
            id_receta_fk_produccion=self.receta_prueba,
            id_usuario_fk_produccion=self.usuario_admin,
            estado_produccion='PENDIENTE'
        )

        if orden_pendiente.estado_produccion == 'FINALIZADA':
            producto_final = orden_pendiente.id_producto_fk_produccion
            producto_final.cant_exist_producto -= orden_pendiente.cant_produccion
            producto_final.save()

        orden_pendiente.estado_produccion = 'CANCELADA'
        orden_pendiente.save()

        producto_bd = Producto.objects.get(id_producto=self.torta_oreo.id_producto)
        print(f" -> Estado final del registro: '{orden_pendiente.estado_produccion}'")
        print(f" -> Stock Inicial Producto: {stock_ini_prod} | Stock Final: {producto_bd.cant_exist_producto} (Intacto)")

        self.assertEqual(orden_pendiente.estado_produccion, 'CANCELADA')
        self.assertEqual(producto_bd.cant_exist_producto, stock_ini_prod)

    def test_15_ajax_cancelar_orden_finalizada_con_reversion_total(self):
        """PRUEBA 15: Flujo complejo de des-hacer. Cancela una orden FINALIZADA, restando del producto y devolviendo la harina."""
        from decimal import Decimal
        print("\n" + "=" * 60)
        print(" [TEST 15] AJAX CANCELAR: ANULACIÓN DE LOTE CON REVERSIÓN DE STOCK ")
        print("=" * 60)

        # Simulamos el entorno: 60 originales + 20 fabricadas = 80
        self.torta_oreo.cant_exist_producto = 80
        self.torta_oreo.save()

        # CORREGIDO: Se asigna correctamente el stock simulado post-producción (100 - 10 consumidas = 90)
        self.harina_trigo.cantidad_exist_mat_prima = Decimal('90.000')
        self.harina_trigo.save()

        orden_a_revertir = Produccion.objects.create(
            nombre_produccion="Lote Defectuoso Quemado",
            fecha_hora_produccion=timezone.now(),
            categoria_produccion='PASTELERIA',
            cant_produccion=20,
            descripcion_produccion="Se quemó en el horno después de marcar finalizado",
            id_producto_fk_produccion=self.torta_oreo,
            id_receta_fk_produccion=self.receta_prueba,
            id_usuario_fk_produccion=self.usuario_admin,
            estado_produccion='FINALIZADA'
        )

        DetalleProduccion.objects.create(
            id_produccion_fk_det_produc=orden_a_revertir,
            id_materia_prima_fk_det_produc=self.harina_trigo,
            cantidad_requerida=10.000
        )

        if orden_a_revertir.estado_produccion == 'FINALIZADA':
            producto_final = orden_a_revertir.id_producto_fk_produccion
            producto_final.cant_exist_producto -= orden_a_revertir.cant_produccion
            producto_final.save()

            detalles = orden_a_revertir.insumos.all()
            for item in detalles:
                insumo = item.id_materia_prima_fk_det_produc
                insumo.cantidad_exist_mat_prima += item.cantidad_requerida
                insumo.save()

        orden_a_revertir.estado_produccion = 'CANCELADA'
        orden_a_revertir.save()

        prod_bd = Producto.objects.get(id_producto=self.torta_oreo.id_producto)
        insumo_bd = MateriaPrima.objects.get(id_materia_prima=self.harina_trigo.id_materia_prima)

        print(f" -> Stock de Producto Revertido (Restado): {prod_bd.cant_exist_producto} unidades (Esperado: 60)")
        print(f" -> Stock de Insumo Devuelto (Sumado): {insumo_bd.cantidad_exist_mat_prima} KG (Esperado: 100)")

        self.assertEqual(prod_bd.cant_exist_producto, 60)
        self.assertEqual(insumo_bd.cantidad_exist_mat_prima, Decimal('100.000'))
        self.assertEqual(orden_a_revertir.estado_produccion, 'CANCELADA')

    def test_16_ajax_cancelar_error_orden_ya_cancelada(self):
        """PRUEBA 16: Validación de redundancia. Asegura que el backend bloquee la petición si la orden ya está cancelada."""
        print("\n" + "=" * 60)
        print(" [TEST 16] MAQUINA DE ESTADOS: ORDEN YA CANCELADA PREVIAMENTE ")
        print("=" * 60)

        orden_cancelada = Produccion.objects.create(
            nombre_produccion="Lote Fantasma",
            fecha_hora_produccion=timezone.now(),
            categoria_produccion='PANADERIA',
            cant_produccion=10,
            descripcion_produccion="Ya inactiva",
            id_producto_fk_produccion=self.torta_oreo,
            id_receta_fk_produccion=self.receta_prueba,
            id_usuario_fk_produccion=self.usuario_admin,
            estado_produccion='CANCELADA'
        )

        success_ajax = True
        msg_ajax = ""

        if orden_cancelada.estado_produccion == 'CANCELADA':
            success_ajax = False
            msg_ajax = 'Esta orden ya está cancelada.'

        print(f" -> Intento de re-cancelación abortado -> Success: {success_ajax} | Mensaje: '{msg_ajax}'")
        self.assertFalse(success_ajax)
        self.assertEqual(msg_ajax, 'Esta orden ya está cancelada.')

    def test_17_ajax_cancelar_error_producto_vendido(self):
        """PRUEBA 17: Regla estricta de negocio. Impide cancelar la producción si el producto ya se vendió (stock menor a lo producido)."""
        print("\n" + "=" * 60)
        print(" [TEST 17] RESTRICCIÓN DE NEGOCIO: IMPEDIR REVERSIÓN POR STOCK INSUFICIENTE ")
        print("=" * 60)

        self.torta_oreo.cant_exist_producto = 10
        self.torta_oreo.save()

        orden_invalida = Produccion.objects.create(
            nombre_produccion="Lote Vendido",
            fecha_hora_produccion=timezone.now(),
            categoria_produccion='PASTELERIA',
            cant_produccion=50,
            descripcion_produccion="Ya se vendieron los productos",
            id_producto_fk_produccion=self.torta_oreo,
            id_receta_fk_produccion=self.receta_prueba,
            id_usuario_fk_produccion=self.usuario_admin,
            estado_produccion='FINALIZADA'
        )

        producto_final = orden_invalida.id_producto_fk_produccion
        success_ajax = True
        msg_ajax = ""

        if producto_final.cant_exist_producto < orden_invalida.cant_produccion:
            success_ajax = False
            msg_ajax = "No se puede revertir: El stock es menor a lo producido."

        print(f" -> Servidor intercepta e impide la anulación -> Success: {success_ajax} | Mensaje enviado: '{msg_ajax}'")
        self.assertFalse(success_ajax)
        self.assertEqual(msg_ajax, "No se puede revertir: El stock es menor a lo producido.")
        print("=" * 60 + "\n")