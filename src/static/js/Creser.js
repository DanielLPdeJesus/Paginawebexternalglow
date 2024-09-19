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
    // Cargar las reservaciones
    cargarReservaciones();

    // Función para mostrar detalles de la reservación
    window.showDetails = function(reservationId) {
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
    };

    // Función para cerrar el modal de detalles
    window.closeModal = function(modalId) {
        var modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
        }
    };

    // Aceptar reservación con SweetAlert2
    window.acceptReservation = function(reservationId) {
        Swal.fire({
            title: '¿Estás seguro?',
            text: "¿Quieres aceptar esta reservación?",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Sí, aceptar',
            cancelButtonText:'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                updateReservationStatus(reservationId, 'aceptada');
                Swal.fire(
                    '¡Aceptada!',
                    'La reservación ha sido aceptada.',
                    'success'
                );
            }
        });
    };

    window.rejectReservation = function(reservationId) {
        Swal.fire({
            title: '¿Estás seguro?',
            text: "¿Quieres rechazar esta reservación?",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Sí, rechazar',
            cancelButtonText:'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                updateReservationStatus(reservationId, 'rechazada');
                Swal.fire(
                    '¡Rechazada!',
                    'La reservación ha sido rechazada.',
                    'success'
                );
            }
        });
    };

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
                throw new Error('Error en la red');
            }
            return response.json(); 
        })
        .then(function(data) {
            if (data.success) {
                var reservationElement = document.querySelector('[data-reservation-id="' + reservationId + '"]');
                if (reservationElement) {
                    reservationElement.remove();
                }
            } else {
                Swal.fire('Error', 'No se pudo actualizar el estado de la reservación.', 'error');
            }
        })
        .catch(function(error) {
            Swal.fire('Error', 'Ocurrió un error al actualizar la reservación.', 'error');
        });
    }
});