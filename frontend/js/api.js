/**
 * API Configuration and Fetch Wrapper
 * Centralized API handling with automatic auth and error management
 */

// API Configuration - change this for different environments
const CONFIG = {
    API_BASE: '', // Empty for same-origin, or set to full URL for different server
    TOKEN_KEY: 'token',
    USERNAME_KEY: 'username'
};

/**
 * Get stored authentication token
 */
function getToken() {
    return localStorage.getItem(CONFIG.TOKEN_KEY);
}

/**
 * Get stored username
 */
function getUsername() {
    return localStorage.getItem(CONFIG.USERNAME_KEY);
}

/**
 * Save authentication data
 */
function saveAuth(token, username) {
    localStorage.setItem(CONFIG.TOKEN_KEY, token);
    localStorage.setItem(CONFIG.USERNAME_KEY, username);
}

/**
 * Clear authentication data and redirect to login
 */
function clearAuth() {
    localStorage.removeItem(CONFIG.TOKEN_KEY);
    localStorage.removeItem(CONFIG.USERNAME_KEY);
    window.location.href = '/index.html';
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!getToken() && !!getUsername();
}

/**
 * Require authentication - redirect to login if not authenticated
 */
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/index.html';
        return false;
    }
    return true;
}

/**
 * Global fetch wrapper with automatic auth headers and error handling
 * @param {string} url - API endpoint
 * @param {object} options - Fetch options
 * @returns {Promise} - Response data or throws error
 */
async function apiFetch(url, options = {}) {
    const token = getToken();

    // Merge headers
    const headers = {
        ...options.headers
    };

    // Add auth header if token exists
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Add content-type for JSON bodies
    if (options.body && typeof options.body === 'string') {
        headers['Content-Type'] = 'application/json';
    }

    try {
        const response = await fetch(`${CONFIG.API_BASE}${url}`, {
            ...options,
            headers
        });

        // Handle authentication errors globally
        if (response.status === 401) {
            clearAuth();
            throw new Error('Sesión expirada. Por favor inicia sesión nuevamente.');
        }

        if (response.status === 403) {
            throw new Error('No tienes permisos para realizar esta acción.');
        }

        // Handle other errors
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || `Error ${response.status}: ${response.statusText}`);
        }

        // Return response for non-JSON responses (like file downloads)
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }

        return response;

    } catch (error) {
        // Re-throw with better message if it's a network error
        if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
            throw new Error('Error de conexión. Verifica tu conexión a internet.');
        }
        throw error;
    }
}

/**
 * Validate password strength
 * @param {string} password - Password to validate
 * @returns {object} - { valid: boolean, message: string }
 */
function validatePassword(password) {
    if (!password || password.length < 6) {
        return { valid: false, message: 'La contraseña debe tener al menos 6 caracteres' };
    }
    if (password.length > 100) {
        return { valid: false, message: 'La contraseña es demasiado larga' };
    }
    return { valid: true, message: '' };
}

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean}
 */
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validate username
 * @param {string} username - Username to validate
 * @returns {object} - { valid: boolean, message: string }
 */
function validateUsername(username) {
    if (!username || username.length < 3) {
        return { valid: false, message: 'El usuario debe tener al menos 3 caracteres' };
    }
    if (username.length > 50) {
        return { valid: false, message: 'El usuario es demasiado largo' };
    }
    if (!/^[a-zA-Z0-9._-]+$/.test(username)) {
        return { valid: false, message: 'El usuario solo puede contener letras, números, puntos, guiones y guiones bajos' };
    }
    return { valid: true, message: '' };
}

/**
 * Escape HTML to prevent XSS (for display purposes only)
 * @param {string} str - String to escape
 * @returns {string} - Escaped string
 */
function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/**
 * Create element safely with text content (prevents XSS)
 * @param {string} tag - HTML tag name
 * @param {string} text - Text content
 * @param {string} className - Optional class name
 * @returns {HTMLElement}
 */
function createSafeElement(tag, text, className = '') {
    const el = document.createElement(tag);
    el.textContent = text;
    if (className) el.className = className;
    return el;
}
