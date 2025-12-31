/**
 * Main Application JavaScript
 * Excel comparison functionality with cancel support and improved error handling
 */

// AbortController for cancellable requests
let currentAbortController = null;

// Check authentication on page load
document.addEventListener('DOMContentLoaded', async () => {
    // Use API wrapper functions if available, otherwise fallback
    const token = typeof getToken === 'function' ? getToken() : localStorage.getItem('token');
    const username = typeof getUsername === 'function' ? getUsername() : localStorage.getItem('username');

    if (!token) {
        window.location.href = '/index.html';
        return;
    }

    // Display username
    document.getElementById('userDisplay').textContent = `Hola, ${username}`;

    // Check if user is admin (try to access admin endpoint)
    try {
        const response = await fetch('/api/users', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
            const adminLink = document.getElementById('adminLink');
            if (adminLink) adminLink.style.display = 'inline-block';
        }
    } catch (e) { /* Not admin, ignore */ }
});

// Logout - use clearAuth if available
document.getElementById('logoutBtn').addEventListener('click', () => {
    if (typeof clearAuth === 'function') {
        clearAuth();
    } else {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.href = '/index.html';
    }
});

// File handling
let file1 = null;
let file2 = null;
let resultBlob = null;

const dropZone1 = document.getElementById('dropZone1');
const dropZone2 = document.getElementById('dropZone2');
const fileInput1 = document.getElementById('file1');
const fileInput2 = document.getElementById('file2');
const fileInfo1 = document.getElementById('fileInfo1');
const fileInfo2 = document.getElementById('fileInfo2');
const compareBtn = document.getElementById('compareBtn');
const progressSection = document.getElementById('progressSection');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Update compare button state
function updateCompareButton() {
    compareBtn.disabled = !(file1 && file2);
}

// Handle file selection for a zone
function handleFileSelect(file, zoneNumber) {
    const validExtensions = ['.xls', '.xlsx'];
    const ext = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));

    if (!validExtensions.includes(ext)) {
        showError('Solo se permiten archivos .xls y .xlsx');
        return;
    }

    const maxSize = 100 * 1024 * 1024; // 100MB
    if (file.size > maxSize) {
        showError('El archivo excede el límite de 100MB');
        return;
    }

    if (zoneNumber === 1) {
        file1 = file;
        updateFileInfo(fileInfo1, file);
        dropZone1.classList.add('hidden');
    } else {
        file2 = file;
        updateFileInfo(fileInfo2, file);
        dropZone2.classList.add('hidden');
    }

    updateCompareButton();
}

// Show error message
function showError(message) {
    errorSection.classList.remove('hidden');
    document.getElementById('errorMessage').textContent = message;
}

// Update file info display
function updateFileInfo(infoElement, file) {
    infoElement.classList.remove('hidden');
    infoElement.querySelector('.file-name').textContent = file.name;
    infoElement.querySelector('.file-size').textContent = formatFileSize(file.size);
}

// Remove file
function removeFile(zoneNumber) {
    if (zoneNumber === 1) {
        file1 = null;
        fileInfo1.classList.add('hidden');
        dropZone1.classList.remove('hidden');
        fileInput1.value = '';
    } else {
        file2 = null;
        fileInfo2.classList.add('hidden');
        dropZone2.classList.remove('hidden');
        fileInput2.value = '';
    }
    updateCompareButton();
}

// Setup drop zone events
function setupDropZone(dropZone, fileInput, zoneNumber) {
    // Click to select
    dropZone.addEventListener('click', () => fileInput.click());

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0], zoneNumber);
        }
    });

    // Drag and drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');

        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0], zoneNumber);
        }
    });
}

// Initialize drop zones
setupDropZone(dropZone1, fileInput1, 1);
setupDropZone(dropZone2, fileInput2, 2);

// Remove buttons
document.querySelectorAll('.btn-remove').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const fileNum = parseInt(btn.dataset.file);
        removeFile(fileNum);
    });
});

// Cancel comparison
function cancelComparison() {
    if (currentAbortController) {
        currentAbortController.abort();
        currentAbortController = null;
    }
    resetCompareState();
}

// Reset compare button state
function resetCompareState() {
    progressSection.classList.add('hidden');
    compareBtn.disabled = false;
    compareBtn.innerHTML = '<span>Comparar Archivos</span><svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M9 5l7 7-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    updateCompareButton();
}

// Compare files
compareBtn.addEventListener('click', async () => {
    if (!file1 || !file2) return;

    // Prevent double click
    if (compareBtn.disabled) return;

    const token = typeof getToken === 'function' ? getToken() : localStorage.getItem('token');
    if (!token) {
        window.location.href = '/index.html';
        return;
    }

    // Create AbortController for cancellation
    currentAbortController = new AbortController();

    // Show progress
    progressSection.classList.remove('hidden');
    resultSection.classList.add('hidden');
    errorSection.classList.add('hidden');
    compareBtn.disabled = true;
    compareBtn.innerHTML = '<span>Procesando...</span>';

    // Create form data
    const formData = new FormData();
    formData.append('file1', file1);
    formData.append('file2', file2);

    try {
        const response = await fetch('/api/compare', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData,
            signal: currentAbortController.signal
        });

        // Handle auth errors
        if (response.status === 401) {
            if (typeof clearAuth === 'function') {
                clearAuth();
            } else {
                localStorage.removeItem('token');
                localStorage.removeItem('username');
                window.location.href = '/index.html';
            }
            return;
        }

        if (response.ok) {
            // Get the blob
            resultBlob = await response.blob();

            // Download automatically
            downloadResult();

            // Show success
            progressSection.classList.add('hidden');
            resultSection.classList.remove('hidden');

        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Error al procesar los archivos');
        }

    } catch (error) {
        progressSection.classList.add('hidden');

        // Don't show error if it was cancelled
        if (error.name === 'AbortError') {
            return;
        }

        errorSection.classList.remove('hidden');
        document.getElementById('errorMessage').textContent = error.message;
    } finally {
        currentAbortController = null;
        resetCompareState();
    }
});

// Download result
function downloadResult() {
    if (!resultBlob) return;

    const url = URL.createObjectURL(resultBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'comparacion_resultado.xlsx';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Download again button
document.getElementById('downloadAgain').addEventListener('click', downloadResult);

// Try again button
document.getElementById('tryAgain').addEventListener('click', () => {
    errorSection.classList.add('hidden');
    removeFile(1);
    removeFile(2);
});

// Cancel button (if exists in HTML)
const cancelBtn = document.getElementById('cancelBtn');
if (cancelBtn) {
    cancelBtn.addEventListener('click', cancelComparison);
}
