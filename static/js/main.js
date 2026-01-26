// Main JavaScript file for common functionality

// Initialize tooltips if Bootstrap is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Add page-specific classes to body for CSS targeting
    // Hide floating button on profile, logout, login, and signup pages
    const path = window.location.pathname;
    if (path.includes('profile') || path.includes('logout') || 
        path.includes('login') || path.includes('signup')) {
        const floatingBtn = document.querySelector('.btn-floating');
        if (floatingBtn) {
            floatingBtn.style.display = 'none';
        }
    }
});

// Common utility functions
function formatCurrency(amount, currency) {
    const symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'INR': '₹',
        'JPY': '¥'
    };
    return `${symbols[currency] || currency} ${parseFloat(amount).toFixed(2)}`;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Handle form submissions with loading states
function setLoadingState(button, isLoading) {
    if (isLoading) {
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
    } else {
        button.disabled = false;
        button.innerHTML = button.getAttribute('data-original-text') || 'Submit';
    }
}

