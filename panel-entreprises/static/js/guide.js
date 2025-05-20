/**
 * guide.js - Gestion de la page guide d'utilisation
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialisation des widgets du guide
    initGuideWidgets();
});

/**
 * Initialise les widgets du guide
 */
function initGuideWidgets() {
    // Animation d'apparition des widgets au scroll
    const widgets = document.querySelectorAll('.guide-widget');
    
    // Ajouter une classe pour l'animation CSS
    widgets.forEach((widget, index) => {
        widget.style.opacity = '0';
        widget.style.transform = 'translateY(20px)';
        
        // Animation avec délai pour effet cascade
        setTimeout(() => {
            widget.style.transition = 'all 0.5s ease';
            widget.style.opacity = '1';
            widget.style.transform = 'translateY(0)';
        }, index * 150); // Délai progressif pour chaque widget
    });
}

// Exportation des fonctions pour une utilisation externe
window.guideApp = {
    initGuideWidgets
};