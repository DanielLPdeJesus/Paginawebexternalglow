setInterval(function() {
    fetch('/Authentication/check_session', { method: 'POST' })
        .then(response => {
            if (!response.ok) {
                window.location.href = '/logout';
            }
        });
}, 300000);

window.addEventListener('beforeunload', function (e) {
    fetch('/logout', { method: 'GET', keepalive: true });
});