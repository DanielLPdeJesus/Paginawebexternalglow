document.addEventListener('DOMContentLoaded', function () {
    var closeButtons = document.querySelectorAll('.close-btn');
    closeButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            this.parentElement.style.display = 'none';
        });
    });

    const togglePassword = document.querySelector('#togglePassword');
    const passwordInput = document.querySelector('#password');

    togglePassword.addEventListener('click', function (e) {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        this.classList.toggle('active');
    });

    const loginForm = document.querySelector('form');
    const loginBtn = document.querySelector('.login-btn');

    loginForm.addEventListener('submit', function (e) {
        loginBtn.disabled = true;
        loginBtn.innerText = 'Procesando...';
    });
});
