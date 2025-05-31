document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const username = this.username.value.trim();
    const password = this.password.value.trim();
    const errorDiv = document.getElementById('loginError');
    errorDiv.style.display = "none";

    if (!username || !password) {
        errorDiv.textContent = "Please enter both username and password.";
        errorDiv.style.display = "block";
        return;
    }

    try {
        const res = await fetch('/api/login/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (data.success) {
            // Redirect to try-on page after successful login
            window.location.href = '/try-on';
        } else {
            errorDiv.textContent = data.message || "Login failed.";
            errorDiv.style.display = "block";
        }
    } catch (err) {
        errorDiv.textContent = "Server error. Please try again.";
        errorDiv.style.display = "block";
    }
});