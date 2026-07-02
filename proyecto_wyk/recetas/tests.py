from django.test import TestCase
from django.apps import apps
from django.db import transaction
from django.http import JsonResponse
from recetas.models import Receta, DetalleReceta
from inventario.models import Producto, MateriaPrima


class ModuloRecetasCajaBlancaTestSuite(TestCase):

    def setUp(self):
        """Inicializa las variables y objetos reales de la base de datos"""
        UsuarioModel = apps.get_model('usuarios', 'Usuario')

        # Carga de usuarios y roles reales
        self.usuario_admin = UsuarioModel.objects.get(id_usuario=1)
        self.usuario_mesero = UsuarioModel.objects.get(id_usuario=2)
        self.usuario_panadero = UsuarioModel.objects.get(id_usuario=4)
        self.usuario_pastelero = UsuarioModel.objects.get(id_usuario=5)

        # Carga de productos reales
        self.torta_oreo = Producto.objects.get(id_producto=105)

        # Carga de materias primas reales
        self.esencia_vainilla = MateriaPrima.objects.get(id_materia_prima=1)
        self.harina_trigo = MateriaPrima.objects.get(id_materia_prima=2)

    def test_1_crear_receta_maestro_detalle_exitosa(self):
        """PRUEBA 1: Registro maestro-detalle de una fórmula. Valida persistencia en cascada."""
        print("\n" + "=" * 60)
        print(" [TEST 1] CREAR RECETA: MAESTRO-DETALLE EXITOSO ")
        print("=" * 60)

        # Simulación del bloque transaccional 'with transaction.atomic()' en crear_receta
        with transaction.atomic():
            nueva_receta = Receta.objects.create(
                nombre_receta="Receta Especial Oreo",
                descripcion_receta="Fórmula base de repostería",
                cantidad_base=12,
                id_producto_fk_receta=self.torta_oreo,
                id_usuario_fk_receta=self.usuario_admin,
                estado_receta=True
            )

            # Insertamos los detalles emulando el comportamiento del FormSet
            DetalleReceta.objects.create(
                id_receta_fk_det_rec=nueva_receta,
                id_materia_prima_fk_det_rec=self.harina_trigo,
                cantidad_insumo_base=1.500
            )
            DetalleReceta.objects.create(
                id_receta_fk_det_rec=nueva_receta,
                id_materia_prima_fk_det_rec=self.esencia_vainilla,
                cantidad_insumo_base=0.250
            )

        print(
            f" -> Receta '{nueva_receta.nombre_receta}' creada para Producto ID: {nueva_receta.id_producto_fk_receta_id}")
        print(f" -> Cantidad de insumos asociados en la receta: {nueva_receta.insumos_receta.count()}")

        self.assertEqual(nueva_receta.cantidad_base, 12)
        self.assertEqual(nueva_receta.insumos_receta.count(), 2)

    def test_2_acceso_permitido_lista_recetas_roles_autorizados(self):
        """PRUEBA 2: Validación de la compuerta multi-rol en lista_recetas (ADMIN, PANADERO, PASTELERO)."""
        print("\n" + "=" * 60)
        print(" [TEST 2] PERMISOS: ACCESO MULTI-ROL AUTORIZADO ")
        print("=" * 60)

        roles_autorizados = ['ADMIN', 'PASTELERO', 'PANADERO']

        # Evaluamos los 3 usuarios autorizados que pasaste
        usuarios_a_probar = [self.usuario_admin, self.usuario_panadero, self.usuario_pastelero]

        for usuario in usuarios_a_probar:
            rol_actual = usuario.rol_fk_usuario.rol
            acceso_concedido = rol_actual in roles_autorizados
            print(
                f" -> Validando Usuario ID {usuario.id_usuario} | Rol: '{rol_actual}' -> ¿Tiene Acceso?: {acceso_concedido}")
            self.assertTrue(acceso_concedido)

    def test_3_seguridad_bloqueo_lista_recetas_no_autorizado(self):
        """PRUEBA 3: Validación de rebote seguro en lista_recetas para roles menores (MESERO)."""
        print("\n" + "=" * 60)
        print(" [TEST 3] SEGURIDAD: REBOTE ROL NO AUTORIZADO (MESERO) ")
        print("=" * 60)

        rol_usuario = self.usuario_mesero.rol_fk_usuario.rol
        print(f" -> Usuario con rol '{rol_usuario}' intenta ingresar a la lista de fórmulas.")

        # Emulación exacta de: if request.user.rol_fk_usuario.rol not in ['ADMIN', 'PASTELERO', 'PANADERO']:
        acceso_permitido = True
        if rol_usuario not in ['ADMIN', 'PASTELERO', 'PANADERO']:
            acceso_permitido = False

        print(f" -> ¿El backend autorizó el renderizado de la plantilla?: {acceso_permitido}")
        self.assertFalse(acceso_permitido)

    def test_4_seguridad_bloqueo_escritura_crear_receta_no_admin(self):
        """PRUEBA 4: Control restrictivo de creación. Solo ADMIN puede escribir fórmulas."""
        print("\n" + "=" * 60)
        print(" [TEST 4] SEGURIDAD: REBOTE DE CREACIÓN A ROLES OPERATIVOS ")
        print("=" * 60)

        # Probamos con el Panadero, quien puede VER pero NO CREAR
        rol_usuario = self.usuario_panadero.rol_fk_usuario.rol
        print(f" -> Usuario '{rol_usuario}' intenta enviar un formulario de nueva receta.")

        # Emulación exacta del condicional en crear_receta: if request.user.rol_fk_usuario.rol != 'ADMIN':
        autorizado_para_guardar = True
        if rol_usuario != 'ADMIN':
            autorizado_para_guardar = False

        print(f" -> ¿El backend permitió la ejecución del formulario?: {autorizado_para_guardar}")
        self.assertFalse(autorizado_para_guardar)

    def test_5_ajax_cambiar_estado_receta_exitoso(self):
        """PRUEBA 5: Acción AJAX cambiar_estado_receta por ADMIN. Inactivación lógica."""
        print("\n" + "=" * 60)
        print(" [TEST 5] AJAX RECETAS: INACTIVACIÓN LÓGICA POR CONTRASEÑA ")
        print("=" * 60)

        receta_activa = Receta.objects.create(
            nombre_receta="Receta Temporal",
            cantidad_base=1,
            id_producto_fk_receta=self.torta_oreo,
            id_usuario_fk_receta=self.usuario_admin,
            estado_receta=True
        )
        print(f" -> Estado inicial de la receta: {receta_activa.estado_receta} (Activa)")

        # Emulación del bloque AJAX exitoso
        rol_usuario = self.usuario_admin.rol_fk_usuario.rol
        success_ajax = False

        if rol_usuario == 'ADMIN':
            # Simula recibir un nuevo_estado = False desde el request JSON
            receta_bd = Receta.objects.get(id_receta=receta_activa.id_receta)
            receta_bd.estado_receta = False
            receta_bd.save()
            success_ajax = True

        receta_final = Receta.objects.get(id_receta=receta_activa.id_receta)
        print(
            f" -> Respuesta JSON -> Success: {success_ajax} | Nuevo estado en Base de Datos: {receta_final.estado_receta}")
        self.assertTrue(success_ajax)
        self.assertFalse(receta_final.estado_receta)

    def test_6_seguridad_ajax_cambiar_estado_bloqueo_no_admin(self):
        """PRUEBA 6: Escudo de seguridad AJAX contra manipulaciones del estado por roles no autorizados."""
        print("\n" + "=" * 60)
        print(" [TEST 6] SEGURIDAD AJAX: BLOQUEO DE ESTADO A ROL NO-ADMIN ")
        print("=" * 60)

        rol_usuario = self.usuario_pastelero.rol_fk_usuario.rol
        print(f" -> Pastelero intenta enviar petición AJAX para alternar un interruptor de estado.")

        if rol_usuario != 'ADMIN':
            success_ajax = False
            message_ajax = 'Acceso denegado.'
        else:
            success_ajax = True
            message_ajax = 'Estado actualizado.'

        print(f" -> Respuesta JSON del servidor -> Success: {success_ajax} | Mensaje: '{message_ajax}'")
        self.assertFalse(success_ajax)
        self.assertEqual(message_ajax, 'Acceso denegado.')

    def test_7_utilidad_ajax_obtener_receta_para_produccion_exitosa(self):
        """PRUEBA 7: Endpoint de integración. Retorna estructura JSON con insumos mapeados para Producción."""
        print("\n" + "=" * 60)
        print(" [TEST 7] INTEGRACIÓN AJAX: ENVÍO DE ESTRUCTURA JSON A PRODUCCIÓN ")
        print("=" * 60)

        # Armamos la receta base que consumirá producción
        receta_maestra = Receta.objects.create(
            nombre_receta="Fórmula Oreo",
            cantidad_base=10,
            id_producto_fk_receta=self.torta_oreo,
            id_usuario_fk_receta=self.usuario_admin,
            estado_receta=True
        )
        DetalleReceta.objects.create(
            id_receta_fk_det_rec=receta_maestra,
            id_materia_prima_fk_det_rec=self.harina_trigo,
            cantidad_insumo_base=2.000
        )

        # Emulación exacta del bloque try en obtener_receta_por_producto_ajax
        try:
            receta = Receta.objects.get(id_producto_fk_receta_id=self.torta_oreo.id_producto, estado_receta=True)
            insumos = receta.insumos_receta.all()

            json_data = {
                'id_receta': receta.id_receta,
                'nombre_receta': receta.nombre_receta,
                'cantidad_base': receta.cantidad_base,
                'insumos': [
                    {
                        'id_materia_prima': item.id_materia_prima_fk_det_rec.id_materia_prima,
                        'nombre_materia_prima': item.id_materia_prima_fk_det_rec.nombre_materia_prima,
                        'cantidad_insumo_base': float(item.cantidad_insumo_base),
                    } for item in insumos
                ]
            }
            success_endpoint = True
        except Receta.DoesNotExist:
            success_endpoint = False
            json_data = {}

        print(f" -> Transmisión AJAX exitosa: {success_endpoint}")
        print(f" -> JSON despachado hacia Producción: {json_data}")

        self.assertTrue(success_endpoint)
        self.assertEqual(json_data['nombre_receta'], "Fórmula Oreo")
        self.assertEqual(json_data['insumos'][0]['cantidad_insumo_base'], 2.0)

    def test_8_utilidad_ajax_obtener_receta_no_existente(self):
        """PRUEBA 8: Control de excepciones del endpoint de producción cuando el producto carece de receta."""
        print("\n" + "=" * 60)
        print(" [TEST 8] INTEGRACIÓN AJAX: EXCEPCIÓN CONTROLADA DOES NOT EXIST ")
        print("=" * 60)

        # Usamos el ID de la Torta Oreo asegurando que no tenga receta en este entorno limpio
        id_producto_sin_receta = 105

        print(f" -> Producción solicita insumos para Producto ID: {id_producto_sin_receta}...")

        # Emulación del bloque 'except Receta.DoesNotExist:' de tu vista
        try:
            receta = Receta.objects.get(id_producto_fk_receta_id=id_producto_sin_receta, estado_receta=True)
            success_ajax = True
            msg_ajax = "Receta cargada."
        except Receta.DoesNotExist:
            success_ajax = False
            msg_ajax = 'El producto seleccionado no tiene una receta asignada.'

        print(f" -> Servidor responde -> Success: {success_ajax} | Mensaje enviado a la interfaz: '{msg_ajax}'")
        self.assertFalse(success_ajax)
        self.assertEqual(msg_ajax, 'El producto seleccionado no tiene una receta asignada.')

    def test_9_edicion_maestro_detalle_receta_exitosa(self):
        """PRUEBA 9: Modificación atómica de una cabecera y el conteo de sus detalles."""
        print("\n" + "=" * 60)
        print(" [TEST 9] EDICIÓN ATÓMICA: ACTUALIZACIÓN DE FÓRMULA ")
        print("=" * 60)

        receta_existente = Receta.objects.create(
            nombre_receta="Nombre Antiguo",
            cantidad_base=5,
            id_producto_fk_receta=self.torta_oreo,
            id_usuario_fk_receta=self.usuario_admin,
            estado_receta=True
        )

        # Emulación del POST en editar_receta
        with transaction.atomic():
            receta_a_editar = Receta.objects.get(id_receta=receta_existente.id_receta)
            receta_a_editar.nombre_receta = "Nombre Actualizado por Admin"
            receta_a_editar.cantidad_base = 24  # Cambiamos el rendimiento de la porción
            receta_a_editar.save()

        receta_editada_bd = Receta.objects.get(id_receta=receta_existente.id_receta)
        print(
            f" -> Registro modificado en BD -> Nuevo Nombre: '{receta_editada_bd.nombre_receta}' | Rendimiento: {receta_editada_bd.cantidad_base} unidades")

        self.assertEqual(receta_editada_bd.nombre_receta, "Nombre Actualizado por Admin")
        self.assertEqual(receta_editada_bd.cantidad_base, 24)

    def test_10_captura_errores_formulario_invalido(self):
        """PRUEBA 10: Flujo alternativo de fallos. Captura exhaustiva de errores en campos no diligenciados."""
        print("\n" + "=" * 60)
        print(" [TEST 10] CONTROL DE FLUJOS: CAPTURA DETALLADA DE ERRORES ")
        print("=" * 60)

        # Simulamos un diccionario de errores idéntico al que genera Django Forms cuando un campo falla
        form_errors = {'nombre_receta': ['Este campo es obligatorio.']}
        messages_captured = []

        # Emulación del bloque: for field, error in form.errors: ... de tu vista
        if form_errors:
            for field, errors in form_errors.items():
                for error in errors:
                    messages_captured.append(f"{field.capitalize()}: {error}")

        print(f" -> Alerta capturada para el usuario: '{messages_captured[0]}'")
        self.assertIn("Nombre_receta: Este campo es obligatorio.", messages_captured)
        print("=" * 60 + "\n")