from django.urls import path
from . import views

urlpatterns = [
    path('inicio/', views.inicio, name='inicio'),
    path('roles/', views.lista_roles, name='lista_roles'),
    path('roles/crear/', views.crear_rol, name='crear_rol'),
    path('roles/editar/<int:id_rol>/', views.editar_rol, name='editar_rol'),
    path('roles/eliminar/<int:id_rol>/', views.eliminar_rol, name='eliminar_rol'),
]