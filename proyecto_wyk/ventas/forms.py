from django import forms
from django.forms import inlineformset_factory
from .models import Venta, DetalleVenta


# --------------------------------- FORMULARIO VENTA ---------------------------------
class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = [
            'numero_mesa',
            'descripcion',
            'estado_pedido',
            'estado_pago'
        ]
        widgets = {
            'numero_mesa': forms.NumberInput(attrs={
                'placeholder': 'N° Mesa (Opcional)',
                'class': 'input-wyk',
                'min': '0'
            }),
            'descripcion': forms.TextInput(attrs={
                'placeholder': 'Ej: Sin cebolla / Para llevar',
                'class': 'input-wyk',
            }),
            'estado_pedido': forms.Select(attrs={
                'class': 'input-wyk',
            }),
            'estado_pago': forms.Select(attrs={
                'class': 'input-wyk',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajustamos valores iniciales
        self.fields['estado_pedido'].initial = 'PENDIENTE'
        self.fields['estado_pago'].initial = 'PENDIENTE'

        # IMPORTANTE: Hacemos que NO sean requeridos en el formulario para evitar
        # errores de validación, ya que los asignamos manualmente en la views.py
        self.fields['estado_pedido'].required = False
        self.fields['estado_pago'].required = False


# --------------------------------- FORMSET DE DETALLE VENTA ---------------------------------

# Este FormSet permite agregar múltiples productos a una sola venta
DetalleVentaFormSet = inlineformset_factory(
    Venta,
    DetalleVenta,
    fields=[
        'id_producto_fk_det_venta',
        'cantidad'
    ],
    widgets={
        'id_producto_fk_det_venta': forms.Select(attrs={
            'class': 'input-wyk select-item producto-select',
            'required': True
        }),
        'cantidad': forms.NumberInput(attrs={
            'class': 'input-wyk cantidad-input',
            'min': '1',
            'placeholder': 'Cant.',
            'required': True
        }),
    },
    extra=0,  # Se maneja dinámicamente con JS en el frontend
    can_delete=True
)