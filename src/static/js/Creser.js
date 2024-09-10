let reservaciones = [];

function cargarReservaciones() {
    if (typeof reservacionesData !== 'undefined' && reservacionesData) {
        try {
            reservaciones = JSON.parse(reservacionesData);
        } catch (error) {
            console.error('Error al parsear reservaciones:', error);
        }
    }
}

cargarReservaciones();

document.addEventListener('DOMContentLoaded', function() {
    let currentReservationId = null;

    cargarReservaciones();

    window.showDetails = function(reservationId) {
        if (!Array.isArray(reservaciones)) {
            return;
        }
        var reservation = reservaciones.find(function(r) { 
            return String(r.id) === String(reservationId); 
        });
        if (reservation) {
            var detailsHtml = 
                '<div class="user-info">' +
                    '<img src="' + (reservation.user_profile_image || '') + '" alt="Foto de perfil" class="w-32 h-32 rounded-full mx-auto">' +
                    '<p><strong>Nombre:</strong> ' + (reservation.user_name || 'N/A') + '</p>' +
                    '<p><strong>Email:</strong> ' + (reservation.user_email || 'N/A') + '</p>' +
                    '<p><strong>Teléfono:</strong> ' + (reservation.user_phone || 'N/A') + '</p>' +
                '</div>' +
                '<div class="reservation-info">' +
                    '<p><strong>Fecha:</strong> ' + (reservation.fecha || 'N/A') + '</p>' +
                    '<p><strong>Hora:</strong> ' + (reservation.hora_seleccionada || 'N/A') + '</p>' +
                    '<p><strong>Servicio:</strong> ' + (reservation.tipo_de_servicio || 'N/A') + '</p>' +
                    '<p><strong>Detalles:</strong> ' + (reservation.peticion || 'N/A') + '</p>' +
                    '<p><strong>Comentarios:</strong> ' + (reservation.comentarios || 'N/A') + '</p>' +
                '</div>' +
                '<div class="reservation-image">' +
                    '<img src="' + (reservation.imagen_url || '') + '" alt="Imagen de la reservación" class="w-full h-auto rounded-lg shadow">' +
                '</div>';
            var detailsElement = document.getElementById('reservationDetails');
            if (detailsElement) {
                detailsElement.innerHTML = detailsHtml;
                document.getElementById('detailsModal').classList.remove('hidden');
            }
        }
    }

    window.showAcceptModal = function(reservationId) {
        currentReservationId = reservationId;
        var modal = document.getElementById('acceptModal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    window.showRejectModal = function(reservationId) {
        currentReservationId = reservationId;
        var modal = document.getElementById('rejectModal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    window.closeModal = function(modalId) {
        var modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    window.acceptReservation = function() {
        if (currentReservationId) {
            updateReservationStatus(currentReservationId, 'aceptada');
        }
    }

    window.rejectReservation = function() {
        if (currentReservationId) {
            updateReservationStatus(currentReservationId, 'rechazada');
        }
    }

    function updateReservationStatus(reservationId, newStatus) {
        fetch('/Authentication/update_reservation_status/' + reservationId, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ status: newStatus }),
        })
        .then(function(response) { 
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json(); 
        })
        .then(function(data) {
            if (data.success) {
                var reservationElement = document.querySelector('[data-reservation-id="' + reservationId + '"]');
                if (reservationElement) {
                    reservationElement.remove();
                }
                closeModal(newStatus === 'aceptada' ? 'acceptModal' : 'rejectModal');
                
                if (document.querySelectorAll('.reservation-item').length === 0) {
                    var agendaElement = document.querySelector('.agenda');
                    if (agendaElement) {
                        agendaElement.innerHTML = '<p class="text-center text-gray-600">No hay citas pendientes.</p>';
                    }
                }
            } else {
                alert('Error al actualizar el estado de la reservación');
            }
        })
        .catch(function(error) {
            alert('Error al actualizar el estado de la reservación');
        });
    }

    document.querySelectorAll('.close').forEach(function(closeBtn) {
        closeBtn.onclick = function() {
            var modal = this.closest('.modal');
            if (modal) {
                modal.classList.add('hidden');
            }
        }
    });

    window.onclick = function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.classList.add('hidden');
        }
    }
});