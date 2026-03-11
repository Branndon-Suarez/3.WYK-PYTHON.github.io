from django.urls import path
from . import views

urlpatterns = [
    # Esta es la URL que llamamos 'inicio' en settings.py
    path('inicio/', views.inicio, name='inicio'),
]