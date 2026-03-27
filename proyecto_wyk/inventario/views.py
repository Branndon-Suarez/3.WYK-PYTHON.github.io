from django.shortcuts import render, redirect
from django.http import JsonResponse

# --- VISTAS TEMPORALES PARA EVITAR ERRORES DE URL ---

def lista_productos(request):
    return render(request, 'inventario/lista_productos.html')

def crear_producto(request):
    return render(request, 'inventario/crear_producto.html')

def editar_producto(request, id_producto):
    pass

def eliminar_producto(request, id_producto):
    pass

def cambiar_estado_producto_ajax(request):
    return JsonResponse({'status': 'ok'})

# --- MATERIA PRIMA ---
def lista_materia_prima(request):
    pass

def crear_materia_prima(request):
    pass

def editar_materia_prima(request, id_materia_prima):
    pass

def eliminar_materia_prima(request, id_materia_prima):
    pass

def cambiar_estado_materia_prima_ajax(request):
    pass

# --- AJUSTES ---
def lista_ajustes_producto(request):
    pass

def crear_ajuste_producto(request):
    pass

def lista_ajustes_materia_prima(request):
    pass

def crear_ajuste_materia_prima(request):
    pass