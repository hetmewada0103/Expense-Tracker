// Signup form validation and submission

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('signupForm');
    const inputs = form.querySelectorAll('input, select');
    
    // Real-time validation
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                validateField(this);
            }
        });
    });
    
    // Password confirmation validation
    const confirmPassword = document.getElementById('confirmPassword');
    confirmPassword.addEventListener('input', function() {
        const password = document.getElementById('password').value;
        if (this.value !== password) {
            this.setCustomValidity('Passwords do not match');
            this.classList.add('is-invalid');
        } else {
            this.setCustomValidity('');
            this.classList.remove('is-invalid');
        }
    });
    
    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Validate all fields
        let isValid = true;
        inputs.forEach(input => {
            if (!validateField(input)) {
                isValid = false;
            }
        });
        
        if (!isValid) {
            return;
        }
        
        // Check password match
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        if (password !== confirmPassword) {
            alert('Passwords do not match');
            return;
        }
        
        // Submit form
        const formData = {
            username: document.getElementById('username').value,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value,
            password: password,
            currency: document.getElementById('currency').value,
            balance: parseFloat(document.getElementById('balance').value)
        };
        
        const response = await fetch('/signup', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        const messageDiv = document.getElementById('signupMessage');
        
        if (data.success) {
            messageDiv.className = 'alert alert-success';
            messageDiv.textContent = data.message;
            messageDiv.classList.remove('d-none');
            setTimeout(() => {
                window.location.href = '/login';
            }, 1500);
        } else {
            messageDiv.className = 'alert alert-danger';
            messageDiv.textContent = data.message;
            messageDiv.classList.remove('d-none');
        }
    });
});

// Field validation functions
function validateField(field) {
    const value = field.value.trim();
    let isValid = true;
    let errorMessage = '';
    
    switch(field.id) {
        case 'username':
            if (value.length < 3 || value.length > 20) {
                isValid = false;
                errorMessage = 'Username must be between 3 and 20 characters';
            } else if (!/^[a-zA-Z0-9_]+$/.test(value)) {
                isValid = false;
                errorMessage = 'Username can only contain letters, numbers, and underscores';
            }
            break;
            
        case 'email':
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid email address';
            }
            break;
            
        case 'phone':
            const phoneRegex = /^\d{10}$/;
            if (!phoneRegex.test(value.replace(/\D/g, ''))) {
                isValid = false;
                errorMessage = 'Phone number must be 10 digits';
            }
            break;
            
        case 'password':
            if (value.length < 8) {
                isValid = false;
                errorMessage = 'Password must be at least 8 characters';
            } else if (!/\d/.test(value)) {
                isValid = false;
                errorMessage = 'Password must contain at least one number';
            }
            break;
            
        case 'confirmPassword':
            const password = document.getElementById('password').value;
            if (value !== password) {
                isValid = false;
                errorMessage = 'Passwords do not match';
            }
            break;
            
        case 'currency':
            if (!value) {
                isValid = false;
                errorMessage = 'Please select a currency';
            }
            break;
            
        case 'balance':
            const balance = parseFloat(value);
            if (isNaN(balance) || balance < 0) {
                isValid = false;
                errorMessage = 'Please enter a valid balance (0 or greater)';
            }
            break;
    }
    
    // Update field styling
    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
        const feedback = field.nextElementSibling;
        if (feedback && feedback.classList.contains('invalid-feedback')) {
            feedback.textContent = '';
        }
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
        const feedback = field.nextElementSibling;
        if (feedback && feedback.classList.contains('invalid-feedback')) {
            feedback.textContent = errorMessage;
        }
    }
    
    return isValid;
}

// Format phone number input
document.addEventListener('DOMContentLoaded', function() {
    const phoneInput = document.getElementById('phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            // Remove non-digits
            let value = e.target.value.replace(/\D/g, '');
            // Limit to 10 digits
            if (value.length > 10) {
                value = value.slice(0, 10);
            }
            e.target.value = value;
        });
    }
});

