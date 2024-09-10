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
                '<div class="bg-white border border-gray-200 rounded-lg shadow-md overflow-hidden">' +
                    '<div class="grid grid-cols-1 md:grid-cols-2 gap-6 p-4">' +
                        '<div class="user-info space-y-4">' +
                            '<img src="' + (reservation.user_profile_image || '') + '" alt="Foto de perfil" class="w-24 h-24 rounded-full mx-auto">' +
                            '<p class="text-gray-700"><span class="font-semibold">Nombre:</span> ' + (reservation.user_name || 'N/A') + '</p>' +
                            '<p class="text-gray-700"><span class="font-semibold">Email:</span> ' + (reservation.user_email || 'N/A') + '</p>' +
                            '<p class="text-gray-700"><span class="font-semibold">Teléfono:</span> ' + (reservation.user_phone || 'N/A') + '</p>' +
                        '</div>' +
                        '<div class="reservation-info space-y-4">' +
                            '<p class="text-gray-700"><span class="font-semibold">Fecha:</span> ' + (reservation.fecha || 'N/A') + '</p>' +
                            '<p class="text-gray-700"><span class="font-semibold">Hora:</span> ' + (reservation.hora_seleccionada || 'N/A') + '</p>' +
                            '<p class="text-gray-700"><span class="font-semibold">Servicio:</span> ' + (reservation.tipo_de_servicio || 'N/A') + '</p>' +
                            '<p class="text-gray-700"><span class="font-semibold">Detalles:</span> ' + (reservation.peticion || 'N/A') + '</p>' +
                            '<p class="text-gray-700"><span class="font-semibold">Comentarios:</span> ' + (reservation.comentarios || 'N/A') + '</p>' +
                        '</div>' +
                    '</div>' +
                    '<div class="reservation-image mt-6 p-4">' +
                        '<img src="' + (reservation.imagen_url || '') + '" alt="Imagen de la reservación" class="w-full h-auto rounded-lg shadow">' +
                    '</div>' +
                '</div>';
            var detailsElement = document.getElementById('reservationDetails');
            if (detailsElement) {
                detailsElement.innerHTML = detailsHtml;
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
                
                // Clear details panel
                var detailsElement = document.getElementById('reservationDetails');
                if (detailsElement) {
                    detailsElement.innerHTML = '<p>Seleccione una reservación para ver los detalles.</p>';
                }
                
                if (document.querySelectorAll('.reservation-item').length === 0) {
                    var reservationsListElement = document.querySelector('.reservations-list');
                    if (reservationsListElement) {
                        reservationsListElement.innerHTML = '<p class="no-reservations">No hay reservaciones aceptadas.</p>';
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