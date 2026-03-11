document.addEventListener('DOMContentLoaded', () => {
    const logoutLink = document.getElementById('logout-link');

    if (logoutLink) {
        logoutLink.addEventListener('click', async (e) => {
            e.preventDefault();

            // 1. Confirmación con SweetAlert2 (usando tu librería ya cargada)
            const result = await Swal.fire({
                title: '¿Cerrar Sesión?',
                text: "¿Estás seguro de que quieres salir del sistema de Panadería WYK?",
                icon: 'question',
                showCancelButton: true,
                confirmButtonColor: '#933e0d', // Color café de tu dashboard.css
                cancelButtonColor: '#64748b',
                confirmButtonText: 'Sí, salir',
                cancelButtonText: 'Cancelar',
                background: document.body.getAttribute('data-theme') === 'dark' ? '#1d0600' : '#fff',
                color: document.body.getAttribute('data-theme') === 'dark' ? '#fff' : '#0f172a'
            });

            if (result.isConfirmed) {
                // 2. Ruta de logout de Django (ajusta si en urls.py pusiste otra)
                const logoutUrl = '/accounts/logout/';

                try {
                    // 3. Obtener el token CSRF que Django puso en el HTML
                    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

                    // 4. Petición POST (Obligatoria en Django por seguridad)
                    const response = await fetch(logoutUrl, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    });

                    // 5. Redirección final
                    if (response.ok || response.redirected) {
                        // Si Django configuró redirect en settings, response.url tendrá la ruta
                        window.location.href = '/accounts/login/';
                    } else {
                        // En caso de error 403 o similar
                        window.location.href = '/accounts/login/';
                    }
                } catch (error) {
                    console.error('Error en logout:', error);
                    Swal.fire('Error', 'No se pudo cerrar la sesión. Intenta de nuevo.', 'error');
                }
            }
        });
    }
});