from django import forms
from .models import Producto, MateriaPrima, AjusteInventario, AjusteIventarioMatPrima

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['id_producto', 'nombre_producto', 'imagen_producto', 'valor_unitario_product',
                  'cant_exist_producto', 'fecha_vencimiento_product', 'tipo_producto', 'estado_producto']
        widgets = {
            'id_producto': forms.NumberInput(attrs={'class': 'form-control'}),
            'nombre_producto': forms.TextInput(attrs={'class': 'form-control'}),
            'imagen_producto': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'valor_unitario_product': forms.NumberInput(attrs={'class': 'form-control'}),
            'cant_exist_producto': forms.NumberInput(attrs={'class': 'form-control'}),
            'fecha_vencimiento_product': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo_producto': forms.Select(attrs={'class': 'form-control'}),
            'estado_producto': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        # Personalización de mensajes de error para campos únicos
        error_messages = {
            'id_producto': {
                'unique': "Ya existe un producto registrado con este ID.",
            },
        }

    def clean_nombre_producto(self):
        nombre = self.cleaned_data.get('nombre_producto').strip().upper()
        if Producto.objects.filter(nombre_producto=nombre).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f"El producto '{nombre}' ya existe.")
        return nombre

class MateriaPrimaForm(forms.ModelForm):
    class Meta:
        model = MateriaPrima
        exclude = ['id_usuario_fk_mat_prima']
        widgets = {
            'id_materia_prima': forms.NumberInput(attrs={'class': 'form-control'}),
            'nombre_materia_prima': forms.TextInput(attrs={'class': 'form-control'}),
            'valor_unitario_mat_prima': forms.NumberInput(attrs={'class': 'form-control'}),
            'fecha_vencimiento_mat_prima': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cantidad_exist_mat_prima': forms.NumberInput(attrs={'class': 'form-control'}),
            'presentacion_mat_prima': forms.TextInput(attrs={'class': 'form-control'}),
            'estado_materia_prima': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        # Personalización de mensajes de error para campos únicos
        error_messages = {
            'id_materia_prima': {
                'unique': "Ya existe una materia prima registrada con este ID.",
            },
        }

    def clean_nombre_materia_prima(self):
        nombre = self.cleaned_data.get('nombre_materia_prima').strip().upper()
        if MateriaPrima.objects.filter(nombre_materia_prima=nombre).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f"La materia prima '{nombre}' ya existe.")
        return nombre