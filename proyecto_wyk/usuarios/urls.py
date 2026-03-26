from django.urls import path
from . import views

urlpatterns = [
    # Ahora sí: dominio.com/usuarios/inicio/
    path('inicio/', views.inicio, name='inicio'),

    # --- RUTAS DE ROLES ---
    path('roles/', views.lista_roles, name='lista_roles'),
    path('roles/crear/', views.crear_rol, name='crear_rol'),
    path('roles/editar/<int:id_rol>/', views.editar_rol, name='editar_rol'),
    path('roles/eliminar/<int:id_rol>/', views.eliminar_rol, name='eliminar_rol'),
    path('roles/cambiar-estado-ajax/', views.cambiar_estado_rol_ajax, name='cambiar_estado_rol_ajax'),

    # --- RUTAS DE USUARIOS ---
    path('usuario/', views.lista_usuarios, name='lista_usuarios'),
    path('usuario/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuario/editar/<int:id_usuario>/', views.editar_usuario, name='editar_usuario'),
    path('usuario/eliminar/<int:id_usuario>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('usuario/cambiar-estado-ajax/', views.cambiar_estado_usuario_ajax, name='cambiar_estado_usuario_ajax'),

    # --- SEGURIDAD ---
    path('verificar-password/', views.verificar_password_ajax, name='verificar_password_ajax'),
]