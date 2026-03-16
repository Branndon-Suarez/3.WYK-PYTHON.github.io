function showModule(name) {
    // 1. Desactivar todos los módulos y botones
    document.querySelectorAll('.module').forEach(m => m.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    // 2. Activar el seleccionado
    const target = document.getElementById('mod-' + name);
    if (target) target.classList.add('active');

    // 3. Activar botón del menú
    const btn = document.querySelector(`.nav-item[onclick*="${name}"]`);
    if (btn) btn.classList.add('active');

    // 4. Cambiar título
    const titles = { dashboard: 'Dashboard', usuarios: 'Usuarios', productos: 'Productos' };
    document.getElementById('pageTitle').textContent = titles[name] || name;
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('collapsed');
}

function updateDateTime() {
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    const el = document.getElementById('dateTime');
    if (el) el.textContent = now.toLocaleDateString('es-CO', options);
}

document.addEventListener('DOMContentLoaded', () => {
    updateDateTime();
    setInterval(updateDateTime, 60000);
});