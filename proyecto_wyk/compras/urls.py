# C:\xampp\htdocs\3.WYK-PYTHON.github.io\proyecto_wyk\compras\urls.py

from django.urls import path
from . import views

urlpatterns = [
    # --- RUTAS DE PROVEEDORES ---
    # dominio.com/compras/proveedores/
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),

    # dominio.com/compras/proveedores/crear/
    path('proveedores/crear/', views.crear_proveedor, name='crear_proveedor'),

    # dominio.com/compras/proveedores/editar/10203040/
    path('proveedores/editar/<int:cedula_proveedor>/', views.editar_proveedor, name='editar_proveedor'),

    # dominio.com/compras/proveedores/eliminar/10203040/
    path('proveedores/eliminar/<int:cedula_proveedor>/', views.eliminar_proveedor, name='eliminar_proveedor'),

    # --- SEGURIDAD Y AJAX ---
    # Ruta para el switch de estado con SweetAlert2 y Contraseña
    path('proveedores/cambiar-estado-ajax/', views.cambiar_estado_proveedor_ajax, name='cambiar_estado_proveedor_ajax'),
]