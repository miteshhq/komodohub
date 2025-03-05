// Theme management
function setTheme(theme) {
    document.documentElement.setAttribute('data-bs-theme', theme);
    localStorage.setItem('theme', theme);

    // Update icon
    const icon = document.querySelector('#themeToggle i');
    icon.className = theme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
}

// Password strength checker with detailed requirements
function checkPasswordStrength(password) {
    const requirements = [
        { regex: /.{8,}/, description: "At least 8 characters" },
        { regex: /[A-Z]/, description: "Contains uppercase letter" },
        { regex: /[a-z]/, description: "Contains lowercase letter" },
        { regex: /[0-9]/, description: "Contains number" },
        { regex: /[^A-Za-z0-9]/, description: "Contains special character" }
    ];

    let strength = 0;
    const meetingReqs = [];

    requirements.forEach(req => {
        if (password.match(req.regex)) {
            strength++;
            meetingReqs.push(req.description);
        }
    });

    return { strength, requirements: meetingReqs };
}

// Initialize theme from localStorage or system preference
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        setTheme(savedTheme);
    } else {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setTheme(prefersDark ? 'dark' : 'light');
    }

    // Theme toggle button
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-bs-theme');
            setTheme(currentTheme === 'dark' ? 'light' : 'dark');
        });
    }

    // Enhanced password strength indicator
    const passwordInput = document.querySelector('input[type="password"]');
    if (passwordInput) {
        const strengthContainer = document.createElement('div');
        strengthContainer.className = 'password-strength-container mt-2';

        const strengthBar = document.createElement('div');
        strengthBar.className = 'password-strength-bar';

        const requirementsList = document.createElement('ul');
        requirementsList.className = 'password-requirements list-unstyled small mt-2';

        passwordInput.parentNode.insertBefore(strengthContainer, passwordInput.nextSibling);
        strengthContainer.appendChild(strengthBar);
        strengthContainer.appendChild(requirementsList);

        passwordInput.addEventListener('input', function() {
            const result = checkPasswordStrength(this.value);
            const percentage = (result.strength / 5) * 100;

            strengthBar.style.width = `${percentage}%`;
            strengthBar.className = 'password-strength-bar';

            if (percentage <= 20) strengthBar.classList.add('very-weak');
            else if (percentage <= 40) strengthBar.classList.add('weak');
            else if (percentage <= 60) strengthBar.classList.add('medium');
            else if (percentage <= 80) strengthBar.classList.add('strong');
            else strengthBar.classList.add('very-strong');

            // Update requirements list
            requirementsList.innerHTML = '';
            result.requirements.forEach(req => {
                const li = document.createElement('li');
                li.innerHTML = `<i class="fas fa-check text-success me-2"></i>${req}`;
                requirementsList.appendChild(li);
            });
        });
    }

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize toasts
    const toastElList = [].slice.call(document.querySelectorAll('.toast'));
    toastElList.map(function (toastEl) {
        return new bootstrap.Toast(toastEl);
    });
});