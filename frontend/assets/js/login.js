document.getElementById('loginForm').addEventListener('submit', function(e) {
    // Example client-side validation (optional)
    const username = this.username.value.trim();
    const password = this.password.value.trim();
    const errorDiv = document.getElementById('loginError');
    if (!username || !password) {
        e.preventDefault();
        errorDiv.textContent = "Please enter both username and password.";
        errorDiv.style.display = "block";
    } else {
        errorDiv.style.display = "none";
    }
});