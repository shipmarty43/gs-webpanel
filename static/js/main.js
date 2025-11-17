// Main JavaScript utilities

// Check authentication
function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token && !window.location.pathname.includes('/login')) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

// API request wrapper
async function apiRequest(url, options = {}) {
    const token = localStorage.getItem('token');

    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        }
    };

    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };

    try {
        const response = await fetch(url, mergedOptions);

        if (response.status === 401) {
            localStorage.removeItem('token');
            window.location.href = '/login';
            throw new Error('Unauthorized');
        }

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Request failed');
        }

        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Logout
async function logout() {
    try {
        await apiRequest('/api/auth/logout', { method: 'POST' });
    } catch (error) {
        console.error('Logout failed:', error);
    } finally {
        // Clear all localStorage data
        localStorage.clear();

        // Clear sessionStorage if used
        sessionStorage.clear();

        // Clear IndexedDB if any
        try {
            if (window.indexedDB && window.indexedDB.databases) {
                const dbs = await window.indexedDB.databases();
                dbs.forEach(db => window.indexedDB.deleteDatabase(db.name));
            }
        } catch (e) {
            console.log('IndexedDB cleanup skipped:', e);
        }

        window.location.href = '/login';
    }
}

// Check storage quota and warn if low
async function checkStorageQuota() {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
        try {
            const estimate = await navigator.storage.estimate();
            const percentUsed = (estimate.usage / estimate.quota) * 100;

            if (percentUsed > 90) {
                console.warn(`Storage quota ${percentUsed.toFixed(1)}% full. Consider clearing browser data.`);
                showWarning('Browser storage is almost full. Please clear your browser cache.');
            }
        } catch (e) {
            console.log('Storage quota check failed:', e);
        }
    }
}

// Clean old cached data from localStorage
function cleanOldCacheData() {
    try {
        // List of keys that should be cleaned
        const keysToCheck = [];

        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            // Clean up any keys that aren't 'token'
            if (key && key !== 'token') {
                keysToCheck.push(key);
            }
        }

        // Remove unnecessary cached data
        keysToCheck.forEach(key => {
            try {
                localStorage.removeItem(key);
            } catch (e) {
                console.log(`Failed to remove ${key}:`, e);
            }
        });
    } catch (e) {
        console.log('Cache cleanup failed:', e);
    }
}

// Show warning message
function showWarning(message) {
    const warningDiv = document.createElement('div');
    warningDiv.className = 'warning-message';
    warningDiv.textContent = message;
    warningDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #ffa657;
        color: #0d1117;
        padding: 15px 20px;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 9999;
        max-width: 400px;
        font-weight: 500;
    `;

    document.body.appendChild(warningDiv);

    setTimeout(() => {
        warningDiv.remove();
    }, 8000);
}

// Format date
function formatDate(dateString) {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Format duration
function formatDuration(ms) {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    const seconds = Math.floor(ms / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
}

// Status indicator
function getStatusIndicator(status) {
    const colors = {
        'online': 'green',
        'offline': 'red',
        'unknown': 'gray',
        'success': 'green',
        'failed': 'red',
        'running': 'blue',
        'pending': 'yellow',
        'completed': 'green',
        'timeout': 'orange'
    };

    const color = colors[status] || 'gray';
    return `<span class="status-dot ${status}"></span><span class="status-${status}">${status}</span>`;
}

// Show error message
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }
}

// Show success message
function showSuccess(message) {
    const successDiv = document.getElementById('success-message');
    if (successDiv) {
        successDiv.textContent = message;
        successDiv.style.display = 'block';
        setTimeout(() => {
            successDiv.style.display = 'none';
        }, 3000);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();

    // Check storage quota on load
    checkStorageQuota();

    // Clean old cached data periodically
    cleanOldCacheData();
});
