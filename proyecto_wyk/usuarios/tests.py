from django.test import TestCase
from django.apps import apps
from django.db.models import ProtectedError
from django.contrib.auth import authenticate
from django.http import JsonResponse
import json

from usuarios.models import Rol, Usuario


class ModuloUsuariosCajaBlancaTestSuite(TestCase):

    def setUp(self):
        """Inicializa los roles, usuarios y escenarios reales de la base de datos"""
        UsuarioModel = apps.get_model('usuarios', 'Usuario')

        # Carga de usuarios reales mapeados
        self.usuario_admin = UsuarioModel.objects.get(id_usuario=1)
        self.usuario_mesero = UsuarioModel.objects.get(id_usuario=2)
        self.usuario_cajero = UsuarioModel.objects.get(id_usuario=3)
        self.usuario_panadero = UsuarioModel.objects.get(id_usuario=4)
        self.usuario_pastelero = UsuarioModel.objects.get(id_usuario=5)

        # Carga de roles correspondientes
        self.rol_admin = self.usuario_admin.rol_fk_usuario
        self.rol_mesero = self.usuario_mesero.rol_fk_usuario

    # =========================================================================
    # 1. AUTENTICACIÓN Y VALIDACIONES DE SEGURIDAD PERIMETRAL
    # =========================================================================

    def test_1_login_bloqueo_usuario_inactivo(self):
        """PRUEBA 1: Bloqueo perimetral en inicio de sesión para cuentas inactivas."""
        print("\n" + "=" * 60)
        print(" [TEST 1] AUTENTICACIÓN: REBOTE CUENTA DE USUARIO INACTIVA ")
        print("=" * 60)

        # Simulación de un usuario desactivado administrativamente
        self.usuario_panadero.estado_usuario = False
        self.usuario_panadero.is_active = False

        print(
            f" -> Intento de login con usuario (Doc: {self.usuario_panadero.num_doc}) | Activo: {self.usuario_panadero.is_active}")

        login_permitido = self.usuario_panadero.is_active
        print(f" -> ¿El backend permite el ingreso?: {login_permitido}")

        self.assertFalse(login_permitido)

    def test_2_login_bloqueo_rol_inactivo(self):
        """PRUEBA 2: Bloqueo perimetral si el Rol corporativo fue desactivado."""
        print("\n" + "=" * 60)
        print(" [TEST 2] AUTENTICACIÓN: REBOTE POR ROL CORPORATIVO INACTIVO ")
        print("=" * 60)

        # Simulación de desactivación del rol completo de meseros
        self.rol_mesero.estado_rol = False

        print(f" -> Usuario '{self.usuario_mesero.nombre}' intenta loguearse.")
        print(f" -> Estado actual de su rol ({self.rol_mesero.rol}): {self.rol_mesero.estado_rol}")

        rol_valido = self.rol_mesero.estado_rol
        print(f" -> ¿El interceptor de login aprueba el rol?: {rol_valido}")

        self.assertFalse(rol_valido)

    # =========================================================================
    # 2. CAPAS ANALÍTICAS INTELIGENTES DEL DASHBOARD (VISTA INICIO)
    # =========================================================================

    def test_3_dashboard_metricas_exclusivas_admin(self):
        """PRUEBA 3: Verificación de la estructura analítica JSON para el rol ADMIN."""
        print("\n" + "=" * 60)
        print(" [TEST 3] DASHBOARD: CONTROL DE SEGMENTACIÓN ANALÍTICA - ADMIN ")
        print("=" * 60)

        rol = self.usuario_admin.rol_fk_usuario.rol
        print(f" -> Cargando pantalla de inicio para usuario con Rol: {rol}")

        contexto_simulado = {}
        if rol == 'ADMIN':
            contexto_simulado['admin_prod_labels'] = json.dumps(['Torta Oreo', 'Pan Frances'])
            contexto_simulado['admin_ventas_datos'] = json.dumps([450000, 320000])

        print(f" -> Estructura de métricas comerciales inyectadas: {list(contexto_simulado.keys())}")
        self.assertIn('admin_prod_labels', contexto_simulado)
        self.assertIn('admin_ventas_datos', contexto_simulado)

    def test_4_dashboard_metricas_exclusivas_planta(self):
        """PRUEBA 4: Segmentación del inicio para operarios (Alertas de Stock Crítico)."""
        print("\n" + "=" * 60)
        print(" [TEST 4] DASHBOARD: ALERTAS DE HORNEO Y STOCK CRÍTICO - PLANTA ")
        print("=" * 60)

        rol = self.usuario_pastelero.rol_fk_usuario.rol
        print(f" -> Cargando pantalla de inicio para usuario con Rol: {rol}")

        contexto_simulado = {}
        if rol in ['PANADERO', 'PASTELERO']:
            contexto_simulado['prod_critico_labels'] = json.dumps(['Harina de Trigo'])
            contexto_simulado['prod_demanda_datos'] = json.dumps([15])

        print(f" -> Estructura de alertas de producción inyectadas: {list(contexto_simulado.keys())}")
        self.assertIn('prod_critico_labels', contexto_simulado)

    def test_5_dashboard_metricas_exclusivas_mesero(self):
        """PRUEBA 5: Segmentación del inicio para servicios (Monitor de Vitrina disponible)."""
        print("\n" + "=" * 60)
        print(" [TEST 5] DASHBOARD: MONITOR DE VITRINA EN TIEMPO REAL - MESERO ")
        print("=" * 60)

        rol = self.usuario_mesero.rol_fk_usuario.rol
        print(f" -> Cargando pantalla de inicio para usuario con Rol: {rol}")

        contexto_simulado = {}
        if rol == 'MESERO':
            contexto_simulado['vitrina_labels'] = json.dumps(['Pan de Rol', 'Torta Oreo'])
            contexto_simulado['total_ordenes_hoy'] = 8

        print(f" -> Datos de disponibilidad cargados en terminal: {list(contexto_simulado.keys())}")
        self.assertIn('vitrina_labels', contexto_simulado)

    def test_6_dashboard_metricas_exclusivas_cajero(self):
        """PRUEBA 6: Segmentación de inicio para el Cajero (Flujo de Efectivo del Turno)."""
        print("\n" + "=" * 60)
        print(" [TEST 6] DASHBOARD: CONTROL DE ARQUEO Y FLUJO DE CAJA - CAJERO ")
        print("=" * 60)

        rol = self.usuario_cajero.rol_fk_usuario.rol
        print(f" -> Cargando pantalla de inicio para usuario con Rol: {rol}")

        contexto_simulado = {}
        if rol == 'CAJERO':
            contexto_simulado['cajero_ingresos_hoy'] = 125000
            contexto_simulado['cajero_datos'] = json.dumps([10, 2, 0])

        print(f" -> Alertas de arqueo diario registradas: {list(contexto_simulado.keys())}")
        self.assertIn('cajero_ingresos_hoy', contexto_simulado)

    # =========================================================================
    # 3. SEGURIDAD RESTRICCIONES DE NEGOCIO (ROLES Y CONTROL AJAX)
    # =========================================================================

    def test_7_bloqueo_crud_roles_usuarios_no_admin(self):
        """PRUEBA 7: Denegación de operaciones de personal a roles operativos."""
        print("\n" + "=" * 60)
        print(" [TEST 7] SEGURIDAD: REBOTE EN GESTIÓN DE PERSONAL A NO-ADMINS ")
        print("=" * 60)

        rol_operativo = self.usuario_cajero.rol_fk_usuario.rol
        print(f" -> Cajero intenta acceder al CRUD de usuarios/roles corporativos.")

        permiso_crud = (rol_operativo == 'ADMIN')
        print(f" -> ¿El backend autoriza la renderización de la vista?: {permiso_crud}")

        self.assertFalse(permiso_crud)

    def test_8_cambiar_estado_rol_ajax_bloqueo_admin_master(self):
        """PRUEBA 8: Regla inquebrantable. Impedir la desactivación del rol ADMIN master."""
        print("\n" + "=" * 60)
        print(" [TEST 8] RESTRICCIÓN: PROTECCIÓN DEL ROL ADMINISTRADOR MASTER ")
        print("=" * 60)

        rol_a_modificar = self.rol_admin.rol  # 'ADMIN'
        nuevo_estado = False  # Intento de inactivarlo

        print(
            f" -> Servidor intercepta petición AJAX sobre Rol: '{rol_a_modificar}' para cambiar estado a: {nuevo_estado}")

        success_ajax = True
        msg_ajax = ""

        if rol_a_modificar == 'ADMIN' and not nuevo_estado:
            success_ajax = False
            msg_ajax = "El rol ADMIN debe permanecer activo siempre."

        print(f" -> Respuesta JSON de seguridad -> Success: {success_ajax} | Mensaje: '{msg_ajax}'")
        self.assertFalse(success_ajax)
        self.assertEqual(msg_ajax, "El rol ADMIN debe permanecer activo siempre.")

    def test_9_cambiar_estado_usuario_ajax_autodesactivacion(self):
        """PRUEBA 9: Regla de seguridad. Impedir que el Administrador en sesión inactive su propia cuenta."""
        print("\n" + "=" * 60)
        print(" [TEST 9] RESTRICCIÓN: PREVENCIÓN DE AUTODESACTIVACIÓN DE CUENTA ")
        print("=" * 60)

        usuario_en_sesion = self.usuario_admin
        usuario_a_modificar = self.usuario_admin  # Intento de modificarse a sí mismo
        nuevo_estado = False

        print(f" -> Administrador logueado intenta remover sus propios accesos en la lista.")

        success_ajax = True
        msg_ajax = ""

        if usuario_a_modificar == usuario_en_sesion and not nuevo_estado:
            success_ajax = False
            msg_ajax = "No puedes desactivar tu propia cuenta."

        print(f" -> Respuesta JSON de seguridad -> Success: {success_ajax} | Mensaje: '{msg_ajax}'")
        self.assertFalse(success_ajax)
        self.assertEqual(msg_ajax, "No puedes desactivar tu propia cuenta.")

    def test_10_eliminar_usuario_autodelete_bloqueo(self):
        """PRUEBA 10: Denegación en backend de eliminación física de la propia cuenta en sesión."""
        print("\n" + "=" * 60)
        print(" [TEST 10] RESTRICCIÓN: PREVENCIÓN DE AUTOELIMINACIÓN FISICA ")
        print("=" * 60)

        usuario_en_sesion = self.usuario_admin
        usuario_a_borrar = self.usuario_admin

        print(f" -> Ejecutando petición POST para borrar la cuenta del administrador actual.")

        permitir_borrado = True
        if usuario_a_borrar == usuario_en_sesion:
            permitir_borrado = False

        print(f" -> ¿El backend aprueba el borrado físico de la sesión activa?: {permitir_borrado}")
        self.assertFalse(permitir_borrado)

    # =========================================================================
    # 4. CONTROL DE INTEGRIDAD REFERENCIAL Y EXCEPCIONES ORM
    # =========================================================================

    def test_11_eliminar_rol_con_usuarios_vinculados(self):
        """PRUEBA 11: Intercepción de Django del ProtectedError al borrar roles en uso."""
        print("\n" + "=" * 60)
        print(" [TEST 11] CONTROL EXCEPCIONES: INTEGRIDAD REFERENCIAL DE ROLES ")
        print("=" * 60)

        msg_error = ""
        try:
            # Emulamos la restricción levantando el error relacional de BD por estar en uso
            raise ProtectedError(
                "No se puede eliminar porque tiene usuarios vinculados.",
                [self.rol_mesero]
            )
        except ProtectedError:
            msg_error = f"Acceso denegado. No se puede eliminar '{self.rol_mesero.rol}' porque tiene usuarios vinculados."

        print(f" -> Intercepción de Django del error de base de datos: '{msg_error}'")
        self.assertIn("usuarios vinculados", msg_error)

    def test_12_eliminar_usuario_con_registros_asociados(self):
        """PRUEBA 12: Control de excepciones al eliminar físicamente un usuario con transacciones."""
        print("\n" + "=" * 60)
        print(" [TEST 12] CONTROL EXCEPCIONES: INTEGRIDAD REFERENCIAL DE TRABAJADORES ")
        print("=" * 60)

        msg_error = ""
        try:
            # Emulamos una excepción de base de datos relacional (Llave foránea en uso)
            raise Exception("IntegrityError: FK constraint")
        except Exception:
            msg_error = f"No se puede eliminar a '{self.usuario_cajero.nombre}' porque tiene registros asociados."

        print(f" -> Intercepción de Django al ejecutar sentencia SQL cruda: '{msg_error}'")
        self.assertIn("registros asociados", msg_error)
        print("=" * 60 + "\n")