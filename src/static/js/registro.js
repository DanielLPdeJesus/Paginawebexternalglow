document.addEventListener('DOMContentLoaded', function() {
    function handleImageUpload(inputId, previewId) {
        const input = document.getElementById(inputId);
        const previewContainer = document.getElementById(previewId);
        
        input.addEventListener('change', function() {
            previewContainer.innerHTML = '';
            if (input.files.length > 0) {
                Array.from(input.files).forEach(file => {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.classList.add('image-preview');
                        previewContainer.appendChild(img);
                    };
                    reader.readAsDataURL(file);
                });
            }
        });
    }

    handleImageUpload('business-image-upload', 'business-image-preview');
    handleImageUpload('service-image-upload', 'service-image-preview');
    handleImageUpload('profile-image-upload', 'profile-image-preview');

    document.getElementById('business_name').addEventListener('input', validateOnlyLettersAndSpaces);
    document.getElementById('owner_name').addEventListener('input', validateOnlyLettersAndSpaces);
    document.getElementById('email').addEventListener('input', validateEmail);
    document.getElementById('password').addEventListener('input', validatePassword);
    document.getElementById('phone').addEventListener('input', validatePhone);
    document.getElementById('address').addEventListener('input', validateAddress);

    const timeFields = ['opening_time_1', 'closing_time_1', 'opening_time_2', 'closing_time_2'];
    timeFields.forEach(fieldId => {
        document.getElementById(fieldId).addEventListener('change', validateAllTimeRanges);
    });

    document.getElementById('registro-form').addEventListener('submit', submitForm);
});

function validateOnlyLettersAndSpaces(event) {
    const input = event.target;
    const errorElement = document.getElementById('error-' + input.id);
    const regex = /^[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ\s]+$/;
    
    if (!regex.test(input.value)) {
        input.classList.add('error-border');
        errorElement.textContent = 'Este campo solo puede contener letras y espacios.';
        errorElement.style.display = 'block';
    } else {
        input.classList.remove('error-border');
        errorElement.style.display = 'none';
    }
}

function validateEmail(event) {
    const input = event.target;
    const errorElement = document.getElementById('error-' + input.id);
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (!regex.test(input.value)) {
        input.classList.add('error-border');
        errorElement.textContent = 'Por favor, ingrese un correo electrónico válido.';
        errorElement.style.display = 'block';
    } else {
        input.classList.remove('error-border');
        errorElement.style.display = 'none';
    }
}

function validatePassword(event) {
    const input = event.target;
    const errorElement = document.getElementById('error-' + input.id);
    const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
    
    if (!regex.test(input.value)) {
        input.classList.add('error-border');
        errorElement.textContent = 'La contraseña debe tener al menos 8 caracteres, incluyendo una mayúscula, una minúscula, un número y un carácter especial.';
        errorElement.style.display = 'block';
    } else {
        input.classList.remove('error-border');
        errorElement.style.display = 'none';
    }
}

function validatePhone(event) {
    const input = event.target;
    const errorElement = document.getElementById('error-' + input.id);
    const regex = /^[0-9]{10}$/;
    
    if (!regex.test(input.value)) {
        input.classList.add('error-border');
        errorElement.textContent = 'El número de teléfono debe contener exactamente 10 dígitos.';
        errorElement.style.display = 'block';
    } else {
        input.classList.remove('error-border');
        errorElement.style.display = 'none';
    }
}

function validateAddress(event) {
    const input = event.target;
    const errorElement = document.getElementById('error-' + input.id);
    
    if (input.value.length < 5) {
        input.classList.add('error-border');
        errorElement.textContent = 'La dirección debe tener al menos 5 caracteres.';
        errorElement.style.display = 'block';
    } else {
        input.classList.remove('error-border');
        errorElement.style.display = 'none';
    }
}

function validateTimeRange(openingId, closingId, errorId, otherOpeningId, otherClosingId) {
    const openingTime = document.getElementById(openingId).value;
    const closingTime = document.getElementById(closingId).value;
    const errorElement = document.getElementById(errorId);
    const otherOpeningTime = document.getElementById(otherOpeningId).value;
    const otherClosingTime = document.getElementById(otherClosingId).value;

    // Verificar que ningún campo esté vacío
    if (!openingTime || !closingTime) {
        errorElement.textContent = 'Ambos campos de hora deben estar completos.';
        errorElement.style.display = 'block';
        return false;
    }

    if (openingTime >= closingTime) {
        errorElement.textContent = 'La hora de apertura debe ser anterior a la hora de cierre.';
        errorElement.style.display = 'block';
        return false;
    }

    if (otherOpeningTime && otherClosingTime) {
        if (
            (openingTime >= otherOpeningTime && openingTime < otherClosingTime) ||
            (closingTime > otherOpeningTime && closingTime <= otherClosingTime) ||
            (openingTime <= otherOpeningTime && closingTime >= otherClosingTime)
        ) {
            errorElement.textContent = 'Los turnos no pueden superponerse.';
            errorElement.style.display = 'block';
            return false;
        }
    }

    errorElement.style.display = 'none';
    return true;
}

function validateAllTimeRanges() {
    const timeValid1 = validateTimeRange('opening_time_1', 'closing_time_1', 'error-turno_1', 'opening_time_2', 'closing_time_2');
    const timeValid2 = validateTimeRange('opening_time_2', 'closing_time_2', 'error-turno_2', 'opening_time_1', 'closing_time_1');
    
    // Verificar que al menos un turno esté completo
    const turno1Completo = document.getElementById('opening_time_1').value && document.getElementById('closing_time_1').value;
    const turno2Completo = document.getElementById('opening_time_2').value && document.getElementById('closing_time_2').value;
    
    if (!turno1Completo && !turno2Completo) {
        document.getElementById('error-turno_1').textContent = 'Debe completar al menos un turno.';
        document.getElementById('error-turno_1').style.display = 'block';
        return false;
    }
    
    return timeValid1 && timeValid2;
}

function nextPart() {
    const fields = document.querySelectorAll('#parte-1 input');
    let isValid = true;

    fields.forEach(field => {
        const errorElement = document.getElementById('error-' + field.id);
        if (!field.checkValidity()) {
            field.classList.add('error-border');
            errorElement.style.display = 'block';
            isValid = false;
        } else {
            field.classList.remove('error-border');
            errorElement.style.display = 'none';
        }
    });

    if (isValid) {
        document.getElementById('parte-1').style.display = 'none';
        document.getElementById('parte-2').style.display = 'block';
    }
}

function prevPart() {
    document.getElementById('parte-1').style.display = 'block';
    document.getElementById('parte-2').style.display = 'none';
}

function submitForm(event) {
    event.preventDefault(); 

    const timeRangesValid = validateAllTimeRanges();

    const imageUploads = [
        { id: 'business-image-upload', minFiles: 3, errorId: 'error-business-images' },
        { id: 'service-image-upload', minFiles: 3, errorId: 'error-service-images' },
        { id: 'profile-image-upload', minFiles: 1, errorId: 'error-profile-image' }
    ];

    let imagesValid = true;
    imageUploads.forEach(upload => {
        const input = document.getElementById(upload.id);
        const errorElement = document.getElementById(upload.errorId);
        if (input.files.length < upload.minFiles) {
            errorElement.style.display = 'block';
            imagesValid = false;
        } else {
            errorElement.style.display = 'none';
        }
    });

    const acceptTerms = document.getElementById('accept-terms');
    const termsError = document.getElementById('error-accept-terms');
    const termsValid = acceptTerms.checked;

    if (!termsValid) {
        termsError.style.display = 'block';
    } else {
        termsError.style.display = 'none';
    }

    const allInputs = document.querySelectorAll('input, select, textarea');
    let allFieldsValid = true;
    allInputs.forEach(input => {
        if (input.type === 'file') return;
        if (input.type === 'checkbox') return;
        
        const errorElement = document.getElementById('error-' + input.id);
        if (!input.checkValidity()) {
            input.classList.add('error-border');
            errorElement.style.display = 'block';
            allFieldsValid = false;
        }
    });

    if (timeRangesValid && imagesValid && termsValid && allFieldsValid) {
        const submitButton = document.getElementById('submit-btn');
        submitButton.disabled = true;
        submitButton.textContent = 'Enviando...';

        event.target.submit();
    } else {
        alert('Por favor, corrija los errores en el formulario antes de enviarlo.');
    }
}