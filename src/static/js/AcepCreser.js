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
                            '<img src="' + (reservation.user_profile_image || '') + '" alt="Foto de perfil" class="w-32 h-32 rounded-full mx-auto">' +
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
                document.getElementById('detailsModal').classList.remove('hidden');
            }
        }
    }

    window.showCancelModal = function(reservationId, fecha, hora, reservationTime) {
        const reservationDateTime = new Date(`${fecha}T${hora}`);
        const currentDateTime = new Date();
        
        const diffInHours = (reservationDateTime - currentDateTime) / (1000 * 60 * 60);
    
        if (diffInHours < 2) {
            Swal.fire({
                title: 'No se puede cancelar',
                text: 'No puedes cancelar la reservación menos de 2 horas antes de la hora programada.',
                icon: 'warning',
                confirmButtonText: 'Aceptar'
            });
            return; 
        }
    
        currentReservationId = reservationId;
        Swal.fire({
            title: '¿Estás seguro?',
            text: `Está por cancelar la reservación del ${fecha} a las ${hora}.`,
            icon: 'warning',
            input: 'textarea',
            inputLabel: 'Razón de la cancelación',
            inputPlaceholder: 'Escribe tu razón aquí...',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sí, cancelar',
            cancelButtonText: 'No, mantener',
            inputValidator: (value) => {
                if (!value) {
                    return '¡Debes escribir una razón!';
                }
            }
        }).then((result) => {
            if (result.isConfirmed) {
                var reason = result.value;
    
                updateReservationStatus(currentReservationId, 'cancelada', reason);
    
                Swal.fire(
                    'Cancelada',
                    'La reservación ha sido cancelada.',
                    'success'
                );
            }
        });
    }

    window.closeModal = function(modalId) {
        var modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
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
                closeModal('detailsModal');
                
                if (document.querySelectorAll('[data-reservation-id]').length === 0) {
                    var reservationsListElement = document.querySelector('ul.space-y-4');
                    if (reservationsListElement) {
                        reservationsListElement.innerHTML = '<p class="text-gray-600">No hay reservaciones aceptadas.</p>';
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
    window.onclick = function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.classList.add('hidden');
        }
    }
});