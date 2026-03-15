from django import forms
from django.contrib.auth.forms import AuthenticationForm


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

    # Error personalizado si el usuario mete letras (gracias al IntegerField)
    error_messages = {
        'invalid_login': "El documento o la contraseña no coinciden.",
        'inactive': "Esta cuenta está inactiva.",
    }