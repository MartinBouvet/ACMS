/**
 * support.js - Gestion de la page support
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialisation du formulaire de contact
    initContactForm();
    
    // Initialisation de l'accordéon FAQ
    initFaqAccordion();
});

/**
 * Initialise le formulaire de contact
 */
function initContactForm() {
    const supportForm = document.getElementById('support-form');
    
    if (supportForm) {
        supportForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Récupérer les données du formulaire
            const formData = {
                name: document.getElementById('name').value,
                email: document.getElementById('email').value,
                subject: document.getElementById('subject').value,
                message: document.getElementById('message').value
            };
            
            // Vérifier que tous les champs sont remplis
            if (!formData.name || !formData.email || !formData.subject || !formData.message) {
                showAlert('error', 'Veuillez remplir tous les champs du formulaire.');
                return;
            }
            
            // Vérifier le format de l'email
            if (!validateEmail(formData.email)) {
                showAlert('error', 'Veuillez entrer une adresse email valide.');
                return;
            }
            
            // Simuler l'envoi du formulaire (pour la démonstration)
            // Dans une implémentation réelle, cette partie serait remplacée par un appel API
            showLoading('Envoi du message en cours...');
            
            setTimeout(() => {
                hideLoading();
                
                // Rediriger vers le client de messagerie avec un email pré-rempli
                const subject = `Support Panel Entreprises - ${formData.subject}`;
                const body = `Bonjour,\n\nJe souhaite contacter le support pour la raison suivante :\n\n${formData.message}\n\nCordialement,\n${formData.name}`;
                
                window.location.href = `mailto:martin.bouvet@edf.fr?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
                
                // Réinitialiser le formulaire
                supportForm.reset();
                
                // Afficher un message de confirmation
                showAlert('success', 'Votre message a été préparé dans votre client de messagerie.');
            }, 1000);
        });
    }
}

/**
 * Initialise l'accordéon de la FAQ
 */
function initFaqAccordion() {
    const accordionHeaders = document.querySelectorAll('.accordion-header');
    
    accordionHeaders.forEach(header => {
        header.addEventListener('click', function() {
            // Récupérer le contenu associé à cet en-tête
            const content = this.nextElementSibling;
            const icon = this.querySelector('.accordion-icon');
            
            // Vérifier si le contenu est actuellement visible
            const isExpanded = content.style.maxHeight !== '0px' && content.style.maxHeight !== '';
            
            // Fermer tous les accordéons
            document.querySelectorAll('.accordion-content').forEach(item => {
                item.style.maxHeight = '0px';
                item.style.padding = '0 1rem';
            });
            
            document.querySelectorAll('.accordion-icon').forEach(icon => {
                icon.textContent = '+';
            });
            
            // Si le contenu n'était pas visible, l'ouvrir
            if (!isExpanded) {
                content.style.maxHeight = content.scrollHeight + 'px';
                content.style.padding = '1rem';
                icon.textContent = '−';
            }
        });
    });
    
    // Initialiser tous les contenus fermés
    document.querySelectorAll('.accordion-content').forEach(content => {
        content.style.maxHeight = '0px';
        content.style.padding = '0 1rem';
    });
}

/**
 * Valide le format d'une adresse email
 * @param {String} email - Adresse email à valider
 * @returns {Boolean} - Vrai si l'email est valide
 */
function validateEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

// Exportation des fonctions pour une utilisation externe
window.supportApp = {
    initContactForm,
    initFaqAccordion
};