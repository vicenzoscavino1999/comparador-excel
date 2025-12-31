/**
 * Admin Panel JavaScript
 * Handles user creation and listing with XSS-safe rendering
 */

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    if (!requireAuth()) return;

    // Display username
    document.getElementById('userDisplay').textContent = getUsername();

    // Setup logout
    document.getElementById('logoutBtn').addEventListener('click', clearAuth);

    // Setup form
    setupCreateUserForm();

    // Load users
    loadUsers();
});

/**
 * Setup create user form with validation
 */
function setupCreateUserForm() {
    const form = document.getElementById('createUserForm');
    const submitBtn = form.querySelector('button[type="submit"]');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const username = document.getElementById('newUsername').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;

        const successMsg = document.getElementById('successMessage');
        const errorMsg = document.getElementById('errorMessage');

        // Hide previous messages
        successMsg.style.display = 'none';
        errorMsg.style.display = 'none';

        // Validate inputs
        const usernameValidation = validateUsername(username);
        if (!usernameValidation.valid) {
            showError(errorMsg, usernameValidation.message);
            return;
        }

        if (!validateEmail(email)) {
            showError(errorMsg, 'Por favor ingresa un correo electrónico válido');
            return;
        }

        const passwordValidation = validatePassword(password);
        if (!passwordValidation.valid) {
            showError(errorMsg, passwordValidation.message);
            return;
        }

        // Disable button to prevent double click
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creando...';

        try {
            await apiFetch('/api/register', {
                method: 'POST',
                body: JSON.stringify({ username, email, password })
            });

            successMsg.textContent = `✅ Usuario "${username}" creado exitosamente`;
            successMsg.style.display = 'block';

            // Clear form
            form.reset();

            // Reload users list
            loadUsers();

        } catch (error) {
            showError(errorMsg, error.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Crear Usuario';
        }
    });
}

/**
 * Show error message
 */
function showError(element, message) {
    element.textContent = `❌ ${message}`;
    element.style.display = 'block';
}

/**
 * Load users list with XSS-safe rendering
 */
async function loadUsers() {
    const loadingEl = document.getElementById('usersLoading');
    const emptyEl = document.getElementById('usersEmpty');
    const tableEl = document.getElementById('usersTable');
    const tbody = document.getElementById('usersBody');

    loadingEl.style.display = 'block';
    emptyEl.style.display = 'none';
    tableEl.style.display = 'none';

    try {
        const data = await apiFetch('/api/users');
        const users = data.users || [];

        loadingEl.style.display = 'none';

        if (!users || users.length === 0) {
            emptyEl.style.display = 'block';
            return;
        }

        // Clear existing rows
        tbody.innerHTML = '';

        // Render users safely (no innerHTML with user data)
        users.forEach(user => {
            const row = document.createElement('tr');

            // Username cell (with strong tag)
            const usernameCell = document.createElement('td');
            const strong = document.createElement('strong');
            strong.textContent = user.username;
            usernameCell.appendChild(strong);
            row.appendChild(usernameCell);

            // Email cell
            const emailCell = document.createElement('td');
            emailCell.textContent = user.email;
            row.appendChild(emailCell);

            // Role badge cell
            const roleCell = document.createElement('td');
            const badge = document.createElement('span');
            badge.className = user.is_admin ? 'badge badge-admin' : 'badge badge-user';
            badge.textContent = user.is_admin ? 'Admin' : 'Usuario';
            roleCell.appendChild(badge);
            row.appendChild(roleCell);

            // Date cell
            const dateCell = document.createElement('td');
            try {
                dateCell.textContent = new Date(user.created_at).toLocaleDateString('es-PE');
            } catch {
                dateCell.textContent = user.created_at || '-';
            }
            row.appendChild(dateCell);

            tbody.appendChild(row);
        });

        tableEl.style.display = 'table';

    } catch (error) {
        loadingEl.textContent = error.message || 'Error al cargar usuarios';
    }
}
