from django.test.runner import DiscoverRunner

class UnmanagedTestRunner(DiscoverRunner):
    """
    Test runner personalizado para evitar que Django intente
    crear, vaciar o destruir la base de datos clonada 'wyk_test'.
    """
    def setup_databases(self, **kwargs):
        # Al dejar esto en pass, Django no tocará ni borrará las tablas clonadas
        pass

    def teardown_databases(self, old_config, **kwargs):
        # Al dejar esto en pass, Django no destruirá la BD al terminar
        pass