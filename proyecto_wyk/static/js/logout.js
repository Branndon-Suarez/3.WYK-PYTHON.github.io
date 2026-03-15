document.addEventListener('DOMContentLoaded', () => {
    const logoutLink = document.getElementById('logout-link');
    const logoutForm = document.getElementById('logout-form');

    if (logoutLink && logoutForm) {
        logoutLink.addEventListener('click', async (e) => {
            e.preventDefault();

            // 1. Confirmación con SweetAlert2
            const result = await Swal.fire({
                title: '¿Cerrar Sesión?',
                text: "¿Estás seguro de que quieres salir del sistema de Panadería WYK?",
                icon: 'question',
                showCancelButton: true,
                confirmButtonColor: '#933e0d', // Color café de tu dashboard
                cancelButtonColor: '#64748b',
                confirmButtonText: 'Sí, salir',
                cancelButtonText: 'Cancelar',
                // Detecta si hay tema oscuro activo
                background: document.body.getAttribute('data-theme') === 'dark' ? '#1d0600' : '#fff',
                color: document.body.getAttribute('data-theme') === 'dark' ? '#fff' : '#0f172a'
            });

            if (result.isConfirmed) {
                // 2. Simplemente enviamos el formulario que ya tiene el CSRF y la URL correcta
                logoutForm.submit();
            }
        });
    }
});