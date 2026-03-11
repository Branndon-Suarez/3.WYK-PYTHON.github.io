from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def inicio(request):
    # Django buscará este archivo en templates/usuarios/inicio.html
    return render(request, 'usuarios/inicio.html')