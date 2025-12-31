// Check if user is already logged in
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (token) {
        // Redirect to app if already logged in
        window.location.href = '/app';
    }
});

// Elements
const loginForm = document.getElementById('loginForm');
const authMessage = document.getElementById('authMessage');

// Show message
function showMessage(message, isError = false) {
    authMessage.textContent = message;
    authMessage.className = `auth-message ${isError ? 'error' : 'success'}`;
    authMessage.classList.remove('hidden');
}

// Hide message
function hideMessage() {
    authMessage.classList.add('hidden');
}

// Login form submission
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideMessage();

    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    const submitBtn = loginForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>Iniciando sesión...</span>';

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('username', username);
            showMessage('¡Inicio de sesión exitoso! Redirigiendo...');
            setTimeout(() => {
                window.location.href = '/app';
            }, 1000);
        } else {
            showMessage(data.detail || 'Error al iniciar sesión', true);
        }
    } catch (error) {
        showMessage('Error de conexión. Intenta de nuevo.', true);
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Iniciar Sesión</span><svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M4 10h12m-4-4l4 4-4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    }
});
