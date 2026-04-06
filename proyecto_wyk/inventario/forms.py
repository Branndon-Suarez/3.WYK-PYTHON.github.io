from django import forms
from .models import Producto, MateriaPrima, AjusteInventario, AjusteInventarioMatPrima

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
        # Se excluye id_materia_prima ya que es autoincremental
        exclude = ['id_materia_prima', 'id_usuario_fk_mat_prima']

        widgets = {
            'nombre_materia_prima': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_vencimiento_mat_prima': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            # step="0.001" permite que el navegador acepte los 3 decimales (gramos/mililitros)
            'cantidad_exist_mat_prima': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            # Cambiado a Select para usar las opciones KG, LT, UN definidas en tu modelo
            'presentacion_mat_prima': forms.Select(attrs={'class': 'form-control'}),
            'descripcion_mat_prima': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'estado_materia_prima': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_nombre_materia_prima(self):
        # Aseguramos que el nombre llegue siempre en Mayúsculas para evitar duplicados
        nombre = self.cleaned_data.get('nombre_materia_prima').strip().upper()
        if MateriaPrima.objects.filter(nombre_materia_prima=nombre).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f"La materia prima '{nombre}' ya existe.")
        return nombre


class AjusteInventarioForm(forms.ModelForm):
    class Meta:
        model = AjusteInventario
        fields = ['tipo_ajuste', 'cantidad_ajustada', 'descripcion']
        widgets = {
            'tipo_ajuste': forms.Select(attrs={'class': 'input-wyk'}),
            'cantidad_ajustada': forms.NumberInput(attrs={'class': 'input-wyk', 'min': '1'}),
            'descripcion': forms.Textarea(attrs={'class': 'input-wyk', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        # Extraemos el producto del constructor para validaciones de stock
        self.producto = kwargs.pop('producto', None)
        super().__init__(*args, **kwargs)

    def clean_cantidad_ajustada(self):
        nueva_cantidad = self.cleaned_data.get('cantidad_ajustada')

        if self.producto:
            # Calculamos el stock base (actual)
            stock_base = self.producto.cant_exist_producto

            # Si estamos editando un registro existente, sumamos lo que ya se había quitado
            if self.instance.pk:
                stock_base += self.instance.cantidad_ajustada

            # Verificación lógica: no se puede quitar más de lo disponible
            if nueva_cantidad > stock_base:
                raise forms.ValidationError(
                    f"Stock insuficiente. El máximo disponible para ajustar es {stock_base}."
                )

        return nueva_cantidad


class AjusteMatPrimaForm(forms.ModelForm):
    class Meta:
        model = AjusteInventarioMatPrima
        # AGREGADO: 'descripcion' a la lista de campos
        fields = ['tipo_ajust_mat', 'cantidad_ajustada_mat', 'descripcion']
        widgets = {
            'tipo_ajust_mat': forms.Select(attrs={'class': 'input-wyk'}),
            'cantidad_ajustada_mat': forms.NumberInput(attrs={
                'class': 'input-wyk',
                'step': '0.001',
                'min': '0.001'
            }),
            # AGREGADO: Widget para la descripción con la clase de tus formularios
            'descripcion': forms.Textarea(attrs={
                'class': 'input-wyk textarea-wyk',
                'placeholder': 'Explique el motivo del cambio...',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        # Extraemos la materia prima para validaciones de stock decimal
        self.materia = kwargs.pop('materia', None)
        super().__init__(*args, **kwargs)

    def clean_cantidad_ajustada_mat(self):
        nueva_cantidad = self.cleaned_data.get('cantidad_ajustada_mat')

        if self.materia:
            # Calculamos el stock base (actual)
            stock_base = self.materia.cantidad_exist_mat_prima

            # Si estamos editando, sumamos el valor anterior para validar el nuevo límite real
            if self.instance.pk:
                stock_base += self.instance.cantidad_ajustada_mat

            if nueva_cantidad > stock_base:
                raise forms.ValidationError(
                    f"Stock insuficiente. El máximo disponible es {stock_base}."
                )

        return nueva_cantidad