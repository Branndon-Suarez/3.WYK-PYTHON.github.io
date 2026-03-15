/**
 * toads-sweetalert2.js
 * Sistema de notificaciones tipo Toast para Panadería WYK
 */

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');

    // 1. VALIDACIÓN DEL LADO DEL CLIENTE (Antes de enviar al servidor)
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const userInput = loginForm.querySelector('input[name="username"]');
            const passwordInput = loginForm.querySelector('input[name="password"]');

            let errorMsg = "";

            // Limpieza y validación básica
            if (!userInput.value.trim() || !passwordInput.value.trim()) {
                errorMsg = "Por favor, completa todos los campos.";
            }
            else if (isNaN(userInput.value)) {
                errorMsg = "El número de documento debe contener solo números.";
            }

            // Si hay error de campos, lanzamos el Toast naranja
            if (errorMsg) {
                e.preventDefault();
                Swal.fire({
                    toast: true,
                    icon: "warning",
                    title: errorMsg,
                    position: "top-end",
                    showConfirmButton: false,
                    timer: 3000,
                    timerProgressBar: true,
                    background: '#f5a623', // Naranja corporativo
                    color: '#fff',         // Texto blanco
                    iconColor: '#fff',     // Icono blanco
                    didOpen: (toast) => {
                        toast.onmouseenter = Swal.stopTimer;
                        toast.onmouseleave = Swal.resumeTimer;
                    }
                });
            }
        });
    }
});

// 2. MANEJO DE MENSAJES QUE VIENEN DESDE DJANGO (Backend)
if (typeof Swal !== 'undefined') {

    // Toast de ÉXITO (Verde Panadería)
    if (typeof successMessage !== 'undefined' && successMessage && successMessage.trim() !== "") {
        Swal.fire({
            toast: true,
            icon: "success",
            title: successMessage,
            position: "top-end",
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            background: '#28a745', // Verde éxito
            color: '#fff',
            iconColor: '#fff',
            didOpen: (toast) => {
                toast.onmouseenter = Swal.stopTimer;
                toast.onmouseleave = Swal.resumeTimer;
            }
        });
    }

    // Toast de ERROR de Servidor/Credenciales (Naranja Corporativo)
    if (typeof errorMessage !== 'undefined' && errorMessage && errorMessage.trim() !== "") {
        Swal.fire({
            toast: true,
            icon: "warning", // Usamos warning para mantener el esquema naranja/blanco
            title: errorMessage,
            position: "top-end",
            showConfirmButton: false,
            timer: 4000, // Un segundo extra para errores de acceso
            timerProgressBar: true,
            background: '#f5a623', // Naranja corporativo
            color: '#fff',         // Texto blanco
            iconColor: '#fff',     // Icono blanco
            didOpen: (toast) => {
                toast.onmouseenter = Swal.stopTimer;
                toast.onmouseleave = Swal.resumeTimer;
            }
        });
    }
}