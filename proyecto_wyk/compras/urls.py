
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

    # --- SEGURIDAD Y AJAX PROVEEDORES ---
    path('proveedores/cambiar-estado-ajax/', views.cambiar_estado_proveedor_ajax, name='cambiar_estado_proveedor_ajax'),

    # --- RUTAS DE COMPRAS (FACTURACIÓN) ---
    # dominio.com/compras/
    path('compra/lista/', views.lista_compras, name='lista_compras'),

    # dominio.com/compras/crear/
    path('compra/crear/', views.crear_compra, name='crear_compra'),

    # dominio.com/compras/detalle/1/
    path('compra/detalle/<int:id_compra>/', views.detalle_compra, name='detalle_compra'),

    # --- SEGURIDAD Y AJAX COMPRAS ---
    # Rutas para cambiar estado de factura (Pagar/Anular) con contraseña
    path('compra/pagar-ajax/', views.pagar_compra_ajax, name='pagar_compra_ajax'),
    path('compra/cancelar-ajax/', views.cancelar_compra_ajax, name='cancelar_compra_ajax'),
]