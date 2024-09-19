
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('contactForm');
    const nombre = document.getElementById('nombre');
    const telefono = document.getElementById('telefono');
    const mensaje = document.getElementById('mensaje');
    const asunto = document.getElementById('asunto');
    const wordCount = document.getElementById('wordCount');

    nombre.addEventListener('input', function(e) {
        this.value = this.value.replace(/[^a-zA-ZáéíóúüñÁÉÍÓÚÜÑ\s]/g, '');
        if (this.value.length > 50) {
            this.value = this.value.slice(0, 50);
        }
    });

    telefono.addEventListener('input', function(e) {
        this.value = this.value.replace(/[^0-9]/g, '');
        if (this.value.length > 10) {
            this.value = this.value.slice(0, 10);
        }
    });

    asunto.addEventListener('input', function(e) {
        if (this.value.length > 30) {
            this.value = this.value.slice(0, 30);
        }
    });

    mensaje.addEventListener('input', function(e) {
        this.value = this.value.replace(/[^a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9\s.,]/g, '');
        let words = this.value.trim().split(/\s+/);
        if (words.length > 75) {
            words = words.slice(0, 75);
            this.value = words.join(' ');
        }
        wordCount.textContent = words.length + ' palabras';
    });

    form.addEventListener('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
        }
    });

    function validateForm() {
        let isValid = true;

        // Check if any field is empty
        const inputs = form.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            if (input.value.trim() === '') {
                alert('Por favor, complete todos los campos.');
                isValid = false;
                return false;
            }
        });

        // Validate name
        if (!/^[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ\s]+$/.test(nombre.value)) {
            alert('El nombre solo puede contener letras y espacios.');
            isValid = false;
        }

        if (nombre.value.length > 50) {
            alert('El nombre no puede tener más de 50 caracteres.');
            isValid = false;
        }

        // Validate phone number
        if (telefono.value.length !== 10) {
            alert('El número de teléfono debe tener 10 dígitos.');
            isValid = false;
        }

        // Validate message
        if (!/^[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ0-9\s.,]+$/.test(mensaje.value)) {
            alert('El mensaje solo puede contener letras, números, espacios, puntos y comas.');
            isValid = false;
        }

        // Validate message length
        let words = mensaje.value.trim().split(/\s+/);
        if (words.length > 75) {
            alert('El mensaje no puede tener más de 75 palabras.');
            isValid = false;
        }

        // Validate subject length
        if (asunto.value.length > 30) {
            alert('El asunto no puede tener más de 30 caracteres.');
            isValid = false;
        }

        return isValid;
    }
});