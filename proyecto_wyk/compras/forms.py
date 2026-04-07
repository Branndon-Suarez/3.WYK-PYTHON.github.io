# C:\xampp\htdocs\3.WYK-PYTHON.github.io\proyecto_wyk\compras\forms.py
from django import forms
from .models import Proveedor

class ProveedorForm(forms.ModelForm):
    # CAMBIO CLAVE: Usamos CharField en lugar de ChoiceField para que Django
    # acepte el texto dinámico que viene de la API sin dar error de "opción no válida".
    lugar_expedicion = forms.CharField(
        widget=forms.Select(attrs={
            'class': 'input-wyk',
            'id': 'id_lugar_expedicion',
            'required': True
        }),
        label="Lugar de Expedición"
    )

    class Meta:
        model = Proveedor
        # No incluimos estado_proveedor ni id_usuario_fk_proveedor
        # ya que se gestionan automáticamente en la vista
        fields = [
            'cedula_proveedor',
            'lugar_expedicion',
            'nombre_proveedor',
            'marca',
            'tel_proveedor',
            'email_proveedor'
        ]
        widgets = {
            'cedula_proveedor': forms.NumberInput(attrs={
                'placeholder': 'Ej: 10203040',
                'class': 'input-wyk',
                'required': True
            }),
            'nombre_proveedor': forms.TextInput(attrs={
                'placeholder': 'Nombre o Razón Social',
                'class': 'input-wyk input-uppercase',
                'required': True
            }),
            'marca': forms.TextInput(attrs={
                'placeholder': 'Nombre Comercial / Marca',
                'class': 'input-wyk input-uppercase',
                'required': True
            }),
            'tel_proveedor': forms.NumberInput(attrs={
                'placeholder': '3101234567',
                'class': 'input-wyk',
                'required': True
            }),
            'email_proveedor': forms.EmailInput(attrs={
                'placeholder': 'proveedor@ejemplo.com',
                'class': 'input-wyk',
                'required': True
            }),
        }

    def __init__(self, *args, **kwargs):
        super(ProveedorForm, self).__init__(*args, **kwargs)
        # Si estamos editando, nos aseguramos de que el campo tenga el valor actual
        if self.instance and self.instance.pk:
            self.fields['lugar_expedicion'].initial = self.instance.lugar_expedicion

    # ------------------------------ VALIDACIONES DE UNICIDAD ------------------------------

    def clean_cedula_proveedor(self):
        cedula = self.cleaned_data.get('cedula_proveedor')
        if Proveedor.objects.filter(cedula_proveedor=cedula).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f"La cédula/NIT '{cedula}' ya está registrado con otro proveedor.")
        return cedula

    def clean_nombre_proveedor(self):
        nombre = self.cleaned_data.get('nombre_proveedor').strip().upper()
        # NUEVA VALIDACIÓN: Verifica si el nombre ya existe
        if Proveedor.objects.filter(nombre_proveedor=nombre).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f"El proveedor '{nombre}' ya existe en el sistema.")
        return nombre

    def clean_tel_proveedor(self):
        telefono = self.cleaned_data.get('tel_proveedor')
        if Proveedor.objects.filter(tel_proveedor=telefono).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f"El teléfono '{telefono}' ya pertenece a otro proveedor.")
        return telefono

    def clean_email_proveedor(self):
        email = self.cleaned_data.get('email_proveedor').strip().lower()
        if Proveedor.objects.filter(email_proveedor=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f"El correo '{email}' ya está registrado.")
        return email