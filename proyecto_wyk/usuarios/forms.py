from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Rol, Usuario

class LoginForm(AuthenticationForm):
    # Usamos IntegerField porque en tu DB num_doc es BIGINT
    username = forms.IntegerField(
        label="Número de Documento",
        widget=forms.NumberInput(attrs={
            'placeholder': 'Tu documento (sin puntos)',
            'class': 'form-control',
            'id': 'username',
            'required': True,
            'autofocus': True
        })
    )

    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'class': 'form-control',
            'id': 'password',
            'required': True
        })
    )

    error_messages = {
        'invalid_login': "El documento o la contraseña no coinciden.",
        'inactive': "Esta cuenta está inactiva.",
    }

# --- NUEVO: Formulario de Roles (AL MISMO NIVEL QUE LOGINFORM) ---
class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ['rol', 'clasificacion']

    def clean_rol(self):
        nombre = self.cleaned_data.get('rol').strip().upper()
        # El exclude(pk=self.instance.pk) permite editar sin que el nombre actual choque consigo mismo
        if Rol.objects.filter(rol=nombre).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f"El rol '{nombre}' ya está registrado.")
        return nombre

# --- NUEVO: Formulario de Usuarios ---
class UsuarioForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Usuario
        fields = ['num_doc', 'nombre', 'email_usuario', 'tel_usuario', 'rol_fk_usuario']

    def clean_num_doc(self):
        doc = self.cleaned_data.get('num_doc')
        if Usuario.objects.filter(num_doc=doc).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f"El documento '{doc}' ya pertenece a otro usuario.")
        return doc

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre').strip()
        if Usuario.objects.filter(nombre=nombre).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f"El nombre '{nombre}' ya está en uso.")
        return nombre

    def clean_email_usuario(self):
        email = self.cleaned_data.get('email_usuario').strip()
        if Usuario.objects.filter(email_usuario=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f"El correo '{email}' ya está registrado.")
        return email

    def clean_tel_usuario(self):
        telefono = self.cleaned_data.get('tel_usuario')
        if telefono:
            # Eliminado .strip() para evitar AttributeError en campos numéricos
            if Usuario.objects.filter(tel_usuario=telefono).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError(f"El teléfono '{telefono}' ya está siendo usado por otro usuario.")
        return telefono