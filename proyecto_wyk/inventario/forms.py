from django import forms
from .models import Producto, MateriaPrima, AjusteInventario, AjusteIventarioMatPrima


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        # SE AGREGA 'descripcion_producto' A LA LISTA
        fields = ['id_producto', 'nombre_producto', 'imagen_producto', 'valor_unitario_product',
                  'cant_exist_producto', 'fecha_vencimiento_product', 'tipo_producto',
                  'descripcion_producto', 'estado_producto']

        widgets = {
            'id_producto': forms.NumberInput(attrs={'class': 'form-control'}),
            'nombre_producto': forms.TextInput(attrs={'class': 'form-control'}),
            'imagen_producto': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'valor_unitario_product': forms.NumberInput(attrs={'class': 'form-control'}),
            'cant_exist_producto': forms.NumberInput(attrs={'class': 'form-control'}),
            'fecha_vencimiento_product': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo_producto': forms.Select(attrs={'class': 'form-control'}),
            # WIDGET PARA LA DESCRIPCIÓN DEL PRODUCTO
            'descripcion_producto': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ej: Notas de sabor o alérgenos...'}),
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
            # Ocultamos el ID si es autoincremental en DB, o lo dejamos si lo digitas manualmente
            'id_materia_prima': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'nombre_materia_prima': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_vencimiento_mat_prima': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            # step="0.001" permite que el navegador acepte los 3 decimales (gramos/mililitros)
            'cantidad_exist_mat_prima': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            # Cambiado a Select para usar las opciones KG, LT, UN definidas en tu modelo
            'presentacion_mat_prima': forms.Select(attrs={'class': 'form-control'}),
            'descripcion_mat_prima': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'estado_materia_prima': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        # Personalización de mensajes de error para campos únicos
        error_messages = {
            'id_materia_prima': {
                'unique': "Ya existe una materia prima registrada con este ID.",
            },
        }

    def clean_nombre_materia_prima(self):
        # Aseguramos que el nombre llegue siempre en Mayúsculas para evitar duplicados
        nombre = self.cleaned_data.get('nombre_materia_prima').strip().upper()
        if MateriaPrima.objects.filter(nombre_materia_prima=nombre).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f"La materia prima '{nombre}' ya existe.")
        return nombre