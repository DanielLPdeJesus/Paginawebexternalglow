// let currentBusinessId = null;

// function cargarDatosNegocio() {
//     if (typeof businessData !== 'undefined' && businessData) {
//         try {
//             businessData = JSON.parse(businessData);
//         } catch (error) {
//             console.error('Error al parsear datos del negocio:', error);
//         }
//     }
// }

// document.addEventListener('DOMContentLoaded', function() {
//     cargarDatosNegocio();

//     window.showEditBusinessModal = function(businessId) {
//         currentBusinessId = businessId;
//         var business = businessData.find(function(b) {
//             return String(b.id) === String(businessId);
//         });
//         if (business) {
//             document.getElementById('editBusinessName').value = business.nombre_negocio || '';
//             document.getElementById('editOwnerName').value = business.nombre_propietario || '';
//             document.getElementById('editAddress').value = business.direccion_negocio || '';
//             document.getElementById('editEmail').value = business.correo || '';
//             document.getElementById('editPhone').value = business.numero_telefono || '';
//             document.getElementById('editHours').value = business.horas_trabajo || '';
//             document.getElementById('editModal').classList.remove('hidden');
//         }
//     }

//     window.saveBusinessDetails = function() {
//         if (currentBusinessId) {
//             var businessName = document.getElementById('editBusinessName').value;
//             var ownerName = document.getElementById('editOwnerName').value;
//             var address = document.getElementById('editAddress').value;
//             var email = document.getElementById('editEmail').value;
//             var phone = document.getElementById('editPhone').value;
//             var hours = document.getElementById('editHours').value;

//             updateBusinessDetails(currentBusinessId, businessName, ownerName, address, email, phone, hours);
//         }
//     }

//     function updateBusinessDetails(businessId, newBusinessName, newOwnerName, newAddress, newEmail, newPhone, newHours) {
//         console.log('Updating business details. ID:', businessId, 'New business name:', newBusinessName, 'New owner name:', newOwnerName, 'New address:', newAddress, 'New email:', newEmail, 'New phone:', newPhone, 'New hours:', newHours);
//         fetch('/Authentication/update_business_details/' + businessId, {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json',
//             },
//             body: JSON.stringify({
//                 nombre_negocio: newBusinessName,
//                 nombre_propietario: newOwnerName,
//                 direccion_negocio: newAddress,
//                 correo: newEmail,
//                 numero_telefono: newPhone,
//                 horas_trabajo: newHours
//             }),
//         })
//         .then(function(response) {
//             if (!response.ok) {
//                 throw new Error('La respuesta de la red no fue correcta');
//             }
//             return response.json();
//         })
//         .then(function(data) {
//             if (data.success) {
//                 console.log('Business details updated successfully');
//                 closeModal('editModal');
//                 // Optionally refresh the business details on the page
//             } else {
//                 console.error('Error updating business details:', data);
//                 alert('Error al actualizar los detalles del negocio');
//             }
//         })
//         .catch(function(error) {
//             console.error('Error:', error);
//             alert('Error al actualizar los detalles del negocio');
//         });
//     }

//     function closeModal(modalId) {
//         var modal = document.getElementById(modalId);
//         if (modal) {
//             modal.classList.add('hidden');
//         }
//     }

//     // Event listener for modal background click
//     window.onclick = function(event) {
//         if (event.target.classList.contains('modal')) {
//             event.target.classList.add('hidden');
//         }
//     }
// });