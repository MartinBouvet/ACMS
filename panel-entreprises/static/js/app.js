// Main JavaScript file
/**
 * app.js - JavaScript principal pour l'application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialiser la barre latérale mobile
    initSidebar();
    
    // Initialiser les notifications
    initNotifications();
    
    // Initialiser les modaux
    initModals();
});

/**
 * Initialise le comportement de la barre latérale mobile
 */
function initSidebar() {
    const mobileToggle = document.querySelector('.mobile-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
        });
        
        // Fermer la barre latérale lors d'un clic à l'extérieur
        document.addEventListener('click', function(e) {
            if (sidebar.classList.contains('open') && 
                !sidebar.contains(e.target) && 
                e.target !== mobileToggle) {
                sidebar.classList.remove('open');
            }
        });
    }
}

/**
 * Initialise le comportement des notifications
 */
function initNotifications() {
    const notificationBtn = document.querySelector('.notification-btn');
    
    if (notificationBtn) {
        notificationBtn.addEventListener('click', function() {
            // Pour le moment, juste un message d'alerte
            showAlert('info', 'Fonctionnalité de notifications à venir');
        });
    }
}

/**
 * Initialise les modaux
 */
function initModals() {
    // Trouver tous les boutons qui ouvrent des modaux
    const modalOpenButtons = document.querySelectorAll('[data-modal]');
    
    modalOpenButtons.forEach(button => {
        const modalId = button.getAttribute('data-modal');
        const modal = document.getElementById(modalId);
        
        if (modal) {
            // Ouvrir le modal au clic
            button.addEventListener('click', function() {
                modal.style.display = 'flex';
            });
            
            // Fermer le modal avec le bouton de fermeture
            const closeButtons = modal.querySelectorAll('.close-button, [data-close-modal]');
            closeButtons.forEach(closeBtn => {
                closeBtn.addEventListener('click', function() {
                    modal.style.display = 'none';
                });
            });
            
            // Fermer le modal en cliquant à l'extérieur
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            });
        }
    });
    
    // Initialiser les modaux spécifiques existants
    initSpecificModals();
}

/**
 * Initialise les modaux spécifiques définis directement dans le HTML
 */
function initSpecificModals() {
    // Modal d'import dans la page base de données
    const importModal = document.getElementById('import-modal');
    const importButton = document.getElementById('import-button');
    const closeImportModal = document.getElementById('close-import-modal');
    const cancelImport = document.getElementById('cancel-import');
    
    if (importModal && importButton) {
        importButton.addEventListener('click', function() {
            importModal.style.display = 'flex';
        });
        
        if (closeImportModal) {
            closeImportModal.addEventListener('click', function() {
                importModal.style.display = 'none';
            });
        }
        
        if (cancelImport) {
            cancelImport.addEventListener('click', function() {
                importModal.style.display = 'none';
            });
        }
        
        // Fermer le modal en cliquant à l'extérieur
        importModal.addEventListener('click', function(e) {
            if (e.target === importModal) {
                importModal.style.display = 'none';
            }
        });
    }
}

/**
 * Affiche une alerte
 * 
 * @param {string} type - Type d'alerte (success, error, warning, info)
 * @param {string} message - Message à afficher
 * @param {number} duration - Durée d'affichage en ms (défaut: 5000)
 */
function showAlert(type, message, duration = 5000) {
    // Créer l'élément d'alerte
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    
    // Définir l'icône selon le type
    let icon = '❓';
    switch (type) {
        case 'success':
            icon = '✅';
            break;
        case 'error':
            icon = '❌';
            break;
        case 'warning':
            icon = '⚠️';
            break;
        case 'info':
            icon = 'ℹ️';
            break;
    }
    
    // Construire le contenu
    alert.innerHTML = `
        <div class="alert-icon">${icon}</div>
        <div class="alert-message">${message}</div>
        <button class="alert-close">×</button>
    `;
    
    // Ajouter au DOM
    document.body.appendChild(alert);
    
    // Gérer la fermeture
    const closeButton = alert.querySelector('.alert-close');
    if (closeButton) {
        closeButton.addEventListener('click', function() {
            if (document.body.contains(alert)) {
                document.body.removeChild(alert);
            }
        });
    }
    
    // Auto-fermeture après la durée spécifiée
    setTimeout(function() {
        if (document.body.contains(alert)) {
            document.body.removeChild(alert);
        }
    }, duration);
}

/**
 * Utilitaire pour formater une date
 * 
 * @param {Date|string} date - Date à formater
 * @param {string} format - Format souhaité (défaut: 'DD/MM/YYYY')
 * @returns {string} - Date formatée
 */
function formatDate(date, format = 'DD/MM/YYYY') {
    const d = new Date(date);
    
    if (isNaN(d.getTime())) {
        return 'Date invalide';
    }
    
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    
    format = format.replace('DD', day);
    format = format.replace('MM', month);
    format = format.replace('YYYY', year);
    format = format.replace('HH', hours);
    format = format.replace('mm', minutes);
    
    return format;
}

/**
 * Affiche l'indicateur de chargement
 * 
 * @param {string} message - Message à afficher
 */
function showLoading(message = 'Chargement en cours...') {
    // Supprimer tout indicateur existant
    hideLoading();
    
    // Créer l'élément de chargement
    const loading = document.createElement('div');
    loading.className = 'loading-overlay';
    loading.innerHTML = `
        <div class="loading-content">
            <div class="spinner"></div>
            <p>${message}</p>
        </div>
    `;
    
    // Ajouter au DOM
    document.body.appendChild(loading);
    document.body.style.overflow = 'hidden';
}

/**
 * Cache l'indicateur de chargement
 */
function hideLoading() {
    const loading = document.querySelector('.loading-overlay');
    if (loading) {
        document.body.removeChild(loading);
        document.body.style.overflow = '';
    }
}

/**
 * Effectue une requête API
 * 
 * @param {string} url - URL de l'API
 * @param {Object} options - Options de fetch
 * @returns {Promise} - Résultat de la requête
 */
async function apiRequest(url, options = {}) {
    try {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        const fetchOptions = { ...defaultOptions, ...options };
        const response = await fetch(url, fetchOptions);
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Erreur API:', error);
        throw error;
    }
}