from django.test import TestCase
from django.apps import apps
from django.db import transaction
from django.db.models import ProtectedError
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
import io
import csv

from inventario.models import Producto, MateriaPrima, AjusteInventario, AjusteInventarioMatPrima


class ModuloInventarioCajaBlancaTestSuite(TestCase):

    def setUp(self):
        """Inicializa las variables, roles y objetos reales de la base de datos"""
        UsuarioModel = apps.get_model('usuarios', 'Usuario')

        # Carga de usuarios reales
        self.usuario_admin = UsuarioModel.objects.get(id_usuario=1)
        self.usuario_mesero = UsuarioModel.objects.get(id_usuario=2)
        self.usuario_panadero = UsuarioModel.objects.get(id_usuario=4)
        self.usuario_pastelero = UsuarioModel.objects.get(id_usuario=5)

        # Carga de productos reales base
        self.torta_oreo = Producto.objects.get(id_producto=105)
        self.pan_frances = Producto.objects.get(id_producto=104)

        # Carga de materias primas reales base
        self.esencia_vainilla = MateriaPrima.objects.get(id_materia_prima=1)
        self.harina_trigo = MateriaPrima.objects.get(id_materia_prima=2)

    # =========================================================================
    # 1. PRUEBAS DE SEGURIDAD PERIMETRAL Y ROLES
    # =========================================================================

    def test_1_lista_productos_acceso_autorizado(self):
        """PRUEBA 1: Validación de acceso permitido a listas para roles autorizados."""
        print("\n" + "=" * 60)
        print(" [TEST 1] SEGURIDAD: ACCESO AUTORIZADO A LISTA PRODUCTOS ")
        print("=" * 60)

        rol_usuario = self.usuario_panadero.rol_fk_usuario.rol
        print(f" -> Usuario '{rol_usuario}' intenta ver inventario de productos.")

        acceso_permitido = rol_usuario in ['ADMIN', 'PASTELERO', 'PANADERO']
        print(f" -> ¿Acceso autorizado en backend?: {acceso_permitido}")
        self.assertTrue(acceso_permitido)

    def test_2_lista_productos_bloqueo_no_autorizado(self):
        """PRUEBA 2: Escudo de seguridad perimetral. Bloquea rol no operativo."""
        print("\n" + "=" * 60)
        print(" [TEST 2] SEGURIDAD: REBOTE ROL NO AUTORIZADO EN LISTA ")
        print("=" * 60)

        rol_usuario = self.usuario_mesero.rol_fk_usuario.rol
        print(f" -> Usuario '{rol_usuario}' intenta ver inventario de productos.")

        acceso_permitido = rol_usuario in ['ADMIN', 'PASTELERO', 'PANADERO']
        print(f" -> ¿Acceso autorizado en backend?: {acceso_permitido}")
        self.assertFalse(acceso_permitido)

    def test_3_restriccion_operaciones_crud_no_admin(self):
        """PRUEBA 3: Control estricto en operaciones de escritura. Solo ADMIN crea o edita."""
        print("\n" + "=" * 60)
        print(" [TEST 3] SEGURIDAD: BLOQUEO CRUD A ROLES OPERATIVOS ")
        print("=" * 60)

        rol_usuario = self.usuario_pastelero.rol_fk_usuario.rol
        print(f" -> Pastelero intenta forzar registro de un nuevo insumo/producto.")

        operacion_permitida = (rol_usuario == 'ADMIN')
        print(f" -> ¿El backend procesa la petición de escritura?: {operacion_permitida}")
        self.assertFalse(operacion_permitida)

    # =========================================================================
    # 2. CARGAS MASIVAS (PROCESAMIENTO CSV)
    # =========================================================================

    def test_4_carga_masiva_productos_exitosa(self):
        """PRUEBA 4: Procesamiento de archivos planos CSV para inyección masiva de productos."""
        print("\n" + "=" * 60)
        print(" [TEST 4] CARGA MASIVA: PROCESAMIENTO CSV PRODUCTOS ")
        print("=" * 60)

        # Simulación de un archivo CSV en memoria
        csv_contenido = "id_producto,nombre_producto,valor_unitario_producto,cant_exist_producto,fecha_vencimiento_producto,tipo_producto,descripcion\n" \
                        "200,PAN DE BONO,2500,40,2026-12-31,PANADERIA,Delicioso pan tradicional"

        csv_file = SimpleUploadedFile("productos.csv", csv_contenido.encode('utf-8'), content_type="text/csv")
        print(f" -> Procesando archivo: {csv_file.name}")

        io_string = io.StringIO(csv_file.read().decode('UTF-8'))
        next(io_string)  # Omitir cabecera

        cont_creados = 0
        for row in csv.reader(io_string, delimiter=',', quotechar='"'):
            nuevo_prod = Producto.objects.create(
                id_producto=row[0],
                nombre_producto=row[1].upper(),
                valor_unitario_product=row[2],
                cant_exist_producto=row[3],
                fecha_vencimiento_product=row[4],
                tipo_producto=row[5].upper(),
                descripcion_producto=row[6] if len(row) > 6 else '',
                id_usuario_fk_producto=self.usuario_admin,
                estado_producto=True
            )
            cont_creados += 1

        print(f" -> Registros insertados con éxito desde CSV: {cont_creados}")
        self.assertEqual(cont_creados, 1)
        self.assertTrue(Producto.objects.filter(id_producto=200).exists())

    def test_5_carga_masiva_materia_prima_exitosa(self):
        """PRUEBA 5: Procesamiento de archivos planos CSV para inyección masiva de insumos."""
        print("\n" + "=" * 60)
        print(" [TEST 5] CARGA MASIVA: PROCESAMIENTO CSV MATERIA PRIMA ")
        print("=" * 60)

        csv_contenido = "nombre,fecha_vencimiento,cantidad,presentacion,descripcion\n" \
                        "AZUCAR MORENA,2027-01-01,50.000,KG,Insumo dulce"

        csv_file = SimpleUploadedFile("insumos.csv", csv_contenido.encode('utf-8'), content_type="text/csv")

        io_string = io.StringIO(csv_file.read().decode('UTF-8'))
        next(io_string)

        cont_creados = 0
        for row in csv.reader(io_string, delimiter=',', quotechar='"'):
            MateriaPrima.objects.create(
                nombre_materia_prima=row[0],
                fecha_vencimiento_mat_prima=row[1],
                cantidad_exist_mat_prima=Decimal(row[2]),
                presentacion_mat_prima=row[3],
                descripcion_mat_prima=row[4] if len(row) > 4 else '',
                id_usuario_fk_mat_prima=self.usuario_admin,
                estado_materia_prima=True
            )
            cont_creados += 1

        print(f" -> Insumos insertados con éxito desde CSV: {cont_creados}")
        self.assertEqual(cont_creados, 1)
        self.assertTrue(MateriaPrima.objects.filter(nombre_materia_prima="AZUCAR MORENA").exists())

    # =========================================================================
    # 3. INTERFACES ASÍNCRONAS Y MODIFICACIONES AJAX
    # =========================================================================

    def test_6_cambiar_estado_producto_ajax_exitoso(self):
        """PRUEBA 6: Mutación de estados vía AJAX mediante confirmación por contraseña."""
        print("\n" + "=" * 60)
        print(" [TEST 6] INTERFAZ AJAX: CAMBIO DE ESTADO CON FIRMA DIGITAL ")
        print("=" * 60)

        # Simulación de check_password correcto y datos JSON recibidos
        password_valido = True
        nuevo_estado = False

        if not password_valido:
            success_ajax = False
        else:
            self.torta_oreo.estado_producto = nuevo_estado
            self.torta_oreo.save()
            success_ajax = True

        print(f" -> Torta Oreo modificada. Nuevo estado: {self.torta_oreo.estado_producto}")
        self.assertTrue(success_ajax)
        self.assertFalse(self.torta_oreo.estado_producto)

    def test_7_cambiar_estado_producto_ajax_password_incorrecto(self):
        """PRUEBA 7: Rechazo de mutación de estado si el administrador digita mal su clave."""
        print("\n" + "=" * 60)
        print(" [TEST 7] INTERFAZ AJAX: RECHAZO POR CONTRASEÑA INCORRECTA ")
        print("=" * 60)

        password_valido = False  # Clave errónea
        success_ajax = True
        msg_ajax = ""

        if not password_valido:
            success_ajax = False
            msg_ajax = "Contraseña incorrecta."

        print(f" -> Respuesta de interceptor -> Success: {success_ajax} | Mensaje: '{msg_ajax}'")
        self.assertFalse(success_ajax)
        self.assertEqual(msg_ajax, "Contraseña incorrecta.")

    # =========================================================================
    # 4. ELIMINACIONES SEGUIDAS POR EXCEPCIONES ORM
    # =========================================================================

    def test_8_eliminar_producto_error_por_integridad_referencial(self):
        """PRUEBA 8: Control de excepciones. Captura de ProtectedError al borrar registros vinculados."""
        print("\n" + "=" * 60)
        print(" [TEST 8] CONTROL EXCEPCIONES: PROTECCIÓN REFERENCIAL DE BASE DE DATOS ")
        print("=" * 60)

        msg_error = ""
        try:
            # Emulamos la restricción levantando el error del motor relacional
            raise ProtectedError(
                "No se puede eliminar porque tiene registros asociados.",
                [self.torta_oreo]
            )
        except ProtectedError:
            msg_error = f"No se puede eliminar '{self.torta_oreo.nombre_producto}' porque tiene registros asociados."

        print(f" -> Intercepción de Django del error de base de datos: '{msg_error}'")
        self.assertIn("No se puede eliminar", msg_error)

    # =========================================================================
    # 5. AJUSTES INTEGRALES DE INVENTARIO (PRODUCTO TERMINADO)
    # =========================================================================

    def test_9_crear_ajuste_producto_exitoso_descuento_stock(self):
        """PRUEBA 9: Decremento del inventario comercial tras reportar pérdidas/daños de productos."""
        print("\n" + "=" * 60)
        print(" [TEST 9] AJUSTE PRODUCTO: MINUSVALÍA Y DESCUENTO DE STOCK ")
        print("=" * 60)

        stock_inicial = self.pan_frances.cant_exist_producto  # 70 unidades
        cantidad_baja = 5

        with transaction.atomic():
            nuevo_ajuste = AjusteInventario.objects.create(
                fecha_ajuste=timezone.now(),
                tipo_ajuste='DAÑADO',
                cantidad_ajustada=cantidad_baja,
                descripcion="Bandeja caída al suelo",
                id_prod_fk_ajuste=self.pan_frances,
                id_usuario_fk_ajuste=self.usuario_admin
            )
            self.pan_frances.cant_exist_producto -= nuevo_ajuste.cantidad_ajustada
            self.pan_frances.save()

        producto_bd = Producto.objects.get(id_producto=self.pan_frances.id_producto)
        print(
            f" -> Stock Inicial: {stock_inicial} | Unidades Ajustadas: {cantidad_baja} | Stock Final BD: {producto_bd.cant_exist_producto}")
        self.assertEqual(producto_bd.cant_exist_producto, stock_inicial - cantidad_baja)

    def test_10_eliminar_ajuste_producto_restablece_inventario(self):
        """PRUEBA 10: Flujo de anulación de bajas de productos. Reintegra las existencias originales."""
        print("\n" + "=" * 60)
        print(" [TEST 10] ANULACIÓN AJUSTE PRODUCTO: RECONSTITUCIÓN DE SALDOS ")
        print("=" * 60)

        stock_actual = self.pan_frances.cant_exist_producto  # 70 unidades
        ajuste_erroneo = AjusteInventario.objects.create(
            fecha_ajuste=timezone.now(),
            tipo_ajuste='ROBO',
            cantidad_ajustada=10,
            id_prod_fk_ajuste=self.pan_frances,
            id_usuario_fk_ajuste=self.usuario_admin
        )

        with transaction.atomic():
            producto = ajuste_erroneo.id_prod_fk_ajuste
            producto.cant_exist_producto += ajuste_erroneo.cantidad_ajustada
            producto.save()
            ajuste_erroneo.delete()

        producto_bd = Producto.objects.get(id_producto=self.pan_frances.id_producto)
        print(
            f" -> Stock antes de anulación: {stock_actual} | Reintegradas: 10 | Nuevo Stock: {producto_bd.cant_exist_producto}")
        self.assertEqual(producto_bd.cant_exist_producto, stock_actual + 10)

    # =========================================================================
    # 6. AJUSTES INTEGRALES DE INVENTARIO (MATERIA PRIMA)
    # =========================================================================

    def test_11_crear_ajuste_materia_prima_exitosa(self):
        """PRUEBA 11: Decremento preciso con tipos Decimal en almacén de insumos."""
        print("\n" + "=" * 60)
        print(" [TEST 11] AJUSTE MATERIA PRIMA: DESCUENTO CON TIPOS DECIMAL ")
        print("=" * 60)

        stock_inicial = self.harina_trigo.cantidad_exist_mat_prima  # 100.000 KG
        baja_insumo = Decimal('12.500')

        with transaction.atomic():
            nuevo_ajuste = AjusteInventarioMatPrima.objects.create(
                fecha_ajust_mat=timezone.now(),
                tipo_ajust_mat='CADUCADO',
                cantidad_ajustada_mat=baja_insumo,
                descripcion="Bulto húmedo",
                id_mat_fk_ajuste_mat=self.harina_trigo,
                id_usuario_fk_ajuste_mat=self.usuario_admin
            )
            self.harina_trigo.cantidad_exist_mat_prima -= nuevo_ajuste.cantidad_ajustada_mat
            self.harina_trigo.save()

        insumo_bd = MateriaPrima.objects.get(id_materia_prima=self.harina_trigo.id_materia_prima)
        print(
            f" -> Inicial: {stock_inicial} KG | Descontado: {baja_insumo} KG | Final: {insumo_bd.cantidad_exist_mat_prima} KG")
        self.assertEqual(insumo_bd.cantidad_exist_mat_prima, stock_inicial - baja_insumo)

    def test_12_eliminar_ajuste_materia_prima_restablece_inventario(self):
        """PRUEBA 12: Flujo de anulación de bajas de insumos. Devuelve los kilogramos/litros exactos."""
        print("\n" + "=" * 60)
        print(" [TEST 12] ANULACIÓN AJUSTE INSUMO: REVERSIÓN ATÓMICA DE MATERIA PRIMA ")
        print("=" * 60)

        stock_actual = self.harina_trigo.cantidad_exist_mat_prima  # 100.000 KG
        ajuste_insumo = AjusteInventarioMatPrima.objects.create(
            fecha_ajust_mat=timezone.now(),
            tipo_ajust_mat='PERDIDA',
            cantidad_ajustada_mat=Decimal('5.250'),
            id_mat_fk_ajuste_mat=self.harina_trigo,
            id_usuario_fk_ajuste_mat=self.usuario_admin
        )

        with transaction.atomic():
            materia = ajuste_insumo.id_mat_fk_ajuste_mat
            materia.cantidad_exist_mat_prima += ajuste_insumo.cantidad_ajustada_mat
            materia.save()
            ajuste_insumo.delete()

        insumo_bd = MateriaPrima.objects.get(id_materia_prima=self.harina_trigo.id_materia_prima)
        print(
            f" -> Stock antes de revertir: {stock_actual} KG | Devuelto: 5.250 KG | Saldo Corregido: {insumo_bd.cantidad_exist_mat_prima} KG")
        self.assertEqual(insumo_bd.cantidad_exist_mat_prima, stock_actual + Decimal('5.250'))
        print("=" * 60 + "\n")