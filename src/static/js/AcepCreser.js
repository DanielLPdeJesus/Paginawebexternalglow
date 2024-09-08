let reservaciones = [];
let currentReservationId = null;

function cargarReservaciones() {
    if (typeof reservacionesData !== 'undefined' && reservacionesData) {
        try {
            reservaciones = JSON.parse(reservacionesData);
        } catch (error) {
            console.error('Error al parsear reservaciones:', error);
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
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
                    '<img src="' + (reservation.user_profile_image || '') + '" alt="Foto de perfil" class="user-profile-image">' +
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
                    '<img src="' + (reservation.imagen_url || '') + '" alt="Imagen de la reservación" class="reservation-photo">' +
                '</div>';
            var detailsElement = document.getElementById('reservationDetails');
            if (detailsElement) {
                detailsElement.innerHTML = detailsHtml;
                document.getElementById('detailsModal').style.display = 'block';
            }
        }
    }

    window.showCancelModal = function(reservationId) {
        currentReservationId = reservationId;
        var modal = document.getElementById('cancelModal');
        if (modal) {
            modal.style.display = 'block';
        }
    }

    window.cancelReservation = function() {
        if (currentReservationId) {
            var reason = document.getElementById('cancelReason').value;
            updateReservationStatus(currentReservationId, 'cancelada', reason);
        }
    }

    window.closeModal = function(modalId) {
        var modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }

    function updateReservationStatus(reservationId, newStatus, reason = '') {
        console.log('Updating reservation status. ID:', reservationId, 'New status:', newStatus, 'Reason:', reason);
        fetch('/Authentication/update_reservation_status_and_comment/' + reservationId, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                status: newStatus,
                reason: reason
            }),
        })
        .then(function(response) { 
            if (!response.ok) {
                throw new Error('La respuesta de la red no fue correcta');
            }
            return response.json(); 
        })
        .then(function(data) {
            if (data.success) {
                console.log('Reservation updated successfully');
                var reservationElement = document.querySelector('[data-reservation-id="' + reservationId + '"]');
                if (reservationElement) {
                    reservationElement.remove();
                }
                closeModal('cancelModal');
                
                if (document.querySelectorAll('.reservation-item').length === 0) {
                    var agendaElement = document.querySelector('.agenda');
                    if (agendaElement) {
                        agendaElement.innerHTML = '<p class="no-reservations">No hay reservaciones aceptadas.</p>';
                    }
                }
            } else {
                console.error('Error updating reservation:', data);
                alert('Error al actualizar el estado de la reservación');
            }
        })
        .catch(function(error) {
            console.error('Error:', error);
            alert('Error al actualizar el estado de la reservación');
        });
    }

    document.querySelectorAll('.close').forEach(function(closeBtn) {
        closeBtn.onclick = function() {
            var modal = this.closest('.modal');
            if (modal) {
                modal.style.display = 'none';
            }
        }
    });

    window.onclick = function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    }
});