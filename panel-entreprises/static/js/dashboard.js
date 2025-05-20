/**
 * dashboard.js - Gestion du tableau de bord
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialiser les composants du tableau de bord
    initDashboard();
});

/**
 * Initialise les composants du tableau de bord
 */
function initDashboard() {
    // Si des boutons d'action sont présents, ajouter les écouteurs d'événements
    const actionButtons = document.querySelectorAll('.activity-actions .button');
    
    actionButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const url = this.getAttribute('href');
            if (url === '#') {
                e.preventDefault();
                alert('Fonctionnalité en cours de développement');
            }
        });
    });
}

// Exporter les fonctions pour une utilisation externe
window.dashboardUtils = {
    initDashboard
};