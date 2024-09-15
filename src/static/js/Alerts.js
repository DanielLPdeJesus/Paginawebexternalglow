
    document.addEventListener('DOMContentLoaded', function() {
        var closeButtons = document.querySelectorAll('.close-btn');
        closeButtons.forEach(function(button) {
            button.addEventListener('click', function() {
                this.parentElement.style.display = 'none';
            });
        });
    });