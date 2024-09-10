
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
});

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

function validateTimeRange(openingId, closingId, errorId) {
    const openingTime = document.getElementById(openingId).value;
    const closingTime = document.getElementById(closingId).value;
    const errorElement = document.getElementById(errorId);

    if (openingTime && closingTime && openingTime >= closingTime) {
        errorElement.style.display = 'block';
        return false;
    } else {
        errorElement.style.display = 'none';
        return true;
    }
}

function submitForm(event) {
    const timeValid1 = validateTimeRange('opening_time_1', 'closing_time_1', 'error-turno_1');
    const timeValid2 = validateTimeRange('opening_time_2', 'closing_time_2', 'error-turno_2');

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

    if (!timeValid1 || !timeValid2 || !imagesValid || !termsValid) {
        event.preventDefault();
        return false;
    }

    return true;
}