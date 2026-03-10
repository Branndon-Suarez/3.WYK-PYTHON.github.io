document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');

    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const userInput = loginForm.querySelector('input[name="username"]');
            const passwordInput = loginForm.querySelector('input[name="password"]');

            let errorMsg = "";

            if (!userInput.value.trim() && !userInput.validity.badInput || !passwordInput.value.trim()) {
                errorMsg = "Por favor, completa todos los campos.";
            }
            else if (userInput.validity.badInput || isNaN(userInput.value)) {
                errorMsg = "El número de documento debe contener solo números.";
            }

            // Si hay un error, detenemos el envío y mostramos SweetAlert
            if (errorMsg) {
                e.preventDefault(); // Evita que el formulario se envíe
                Swal.fire({
                    toast: true,
                    icon: "warning",
                    title: errorMsg,
                    position: "top-end",
                    showConfirmButton: false,
                    timer: 3000,
                    timerProgressBar: true
                });
            }
        });
    }
});

// ... aquí sigue el código que ya tenías de successMessage y errorMessage ...

if (typeof Swal !== 'undefined') {
    // Si la variable existe y tiene texto (Éxito)
    if (typeof successMessage !== 'undefined' && successMessage) {
        Swal.fire({
            toast: true,
            icon: "success",
            title: successMessage,
            position: "top-end",
            showConfirmButton: false,
            timer: 2000,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.onmouseenter = Swal.stopTimer;
                toast.onmouseleave = Swal.resumeTimer;
            }
        });
    }

    // Si la variable existe y tiene texto (Error)
    if (typeof errorMessage !== 'undefined' && errorMessage) {
        Swal.fire({
            toast: true,
            icon: "error",
            title: errorMessage,
            position: "top-end",
            showConfirmButton: false,
            timer: 2000,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.onmouseenter = Swal.stopTimer;
                toast.onmouseleave = Swal.resumeTimer;
            }
        });
    }
}