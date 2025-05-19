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
    // Ajouter un effet de zoom sur les images des widgets
    const widgetImages = document.querySelectorAll('.widget-image img');
    
    widgetImages.forEach(img => {
        img.addEventListener('click', function() {
            // Créer une modal pour afficher l'image en grand
            const modal = document.createElement('div');
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content image-preview-modal">
                    <div class="modal-header">
                        <h3>${this.alt}</h3>
                        <button class="close-button">&times;</button>
                    </div>
                    <div class="modal-body image-preview-body">
                        <img src="${this.src}" alt="${this.alt}" class="preview-image">
                    </div>
                </div>
            `;
            
            // Ajouter la modal au DOM
            document.body.appendChild(modal);
            
            // Gérer la fermeture de la modal
            const closeButton = modal.querySelector('.close-button');
            
            closeButton.addEventListener('click', function() {
                document.body.removeChild(modal);
            });
            
            // Fermer la modal en cliquant à l'extérieur
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    document.body.removeChild(modal);
                }
            });
        });
        
        // Ajouter une classe pour indiquer que l'image est cliquable
        img.classList.add('clickable');
    });
    
    // Animation d'apparition des widgets au scroll
    const widgets = document.querySelectorAll('.guide-widget');
    
    // Fonction pour vérifier si un élément est visible dans la fenêtre
    function isElementInViewport(el) {
        const rect = el.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
    
    // Fonction pour animer les widgets visibles
    function animateVisibleWidgets() {
        widgets.forEach(widget => {
            if (isElementInViewport(widget) && !widget.classList.contains('animated')) {
                widget.classList.add('animated');
                widget.style.animation = 'fadeInUp 0.5s ease-out forwards';
            }
        });
    }
    
    // Vérifier au chargement et au scroll
    animateVisibleWidgets();
    window.addEventListener('scroll', animateVisibleWidgets);
}

// Exportation des fonctions pour une utilisation externe
window.guideApp = {
    initGuideWidgets
};