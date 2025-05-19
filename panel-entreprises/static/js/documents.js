/**
 * documents.js - Gestion des documents types
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialiser les filtres
    initDocumentFilters();
    
    // Initialiser les modaux
    initDocumentModals();
    
    // Initialiser les actions des documents
    initDocumentActions();
});

/**
 * Initialise les filtres de documents
 */
function initDocumentFilters() {
    const typeFilter = document.getElementById('document-type-filter');
    const searchInput = document.getElementById('document-search');
    
    if (typeFilter) {
        typeFilter.addEventListener('change', function() {
            filterDocuments();
        });
    }
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filterDocuments();
        });
        
        // Bouton de recherche
        const searchButton = document.querySelector('.search-button');
        if (searchButton) {
            searchButton.addEventListener('click', function() {
                filterDocuments();
            });
        }
    }
}

/**
 * Filtre les documents selon les critères
 */
function filterDocuments() {
    const typeFilter = document.getElementById('document-type-filter');
    const searchInput = document.getElementById('document-search');
    
    const typeValue = typeFilter ? typeFilter.value : 'all';
    const searchValue = searchInput ? searchInput.value.toLowerCase() : '';
    
    const documentCards = document.querySelectorAll('.document-card');
    
    documentCards.forEach(card => {
        const documentType = card.getAttribute('data-type');
        const documentTitle = card.querySelector('h3').textContent.toLowerCase();
        
        // Vérifier si le document correspond au filtre de type
        const matchesType = typeValue === 'all' || documentType === typeValue;
        
        // Vérifier si le document correspond à la recherche
        const matchesSearch = searchValue === '' || documentTitle.includes(searchValue);
        
        // Afficher ou masquer le document
        if (matchesType && matchesSearch) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
    
    // Vérifier s'il y a des documents visibles
    const visibleCards = document.querySelectorAll('.document-card[style="display: flex;"]');
    const documentsGrid = document.querySelector('.documents-grid');
    
    if (visibleCards.length === 0 && documentsGrid) {
        // Aucun document visible, afficher un message
        if (!document.querySelector('.no-results')) {
            const noResults = document.createElement('div');
            noResults.className = 'empty-state no-results';
            noResults.innerHTML = `
                <div class="empty-icon">🔍</div>
                <p>Aucun document ne correspond à votre recherche.</p>
                <button class="button secondary reset-filters">Réinitialiser les filtres</button>
            `;
            documentsGrid.appendChild(noResults);
            
            // Ajouter un écouteur pour le bouton de réinitialisation
            const resetButton = noResults.querySelector('.reset-filters');
            if (resetButton) {
                resetButton.addEventListener('click', function() {
                    if (typeFilter) typeFilter.value = 'all';
                    if (searchInput) searchInput.value = '';
                    filterDocuments();
                });
            }
        }
    } else {
        // Supprimer le message de résultats vides s'il existe
        const noResults = document.querySelector('.no-results');
        if (noResults) {
            noResults.parentNode.removeChild(noResults);
        }
    }
}

/**
 * Initialise les modaux de documents
 */
function initDocumentModals() {
    // Modal d'ajout de document
    const uploadButton = document.getElementById('upload-document-button');
    const uploadModal = document.getElementById('upload-document-modal');
    
    if (uploadButton && uploadModal) {
        // Ouvrir le modal
        uploadButton.addEventListener('click', function() {
            uploadModal.style.display = 'flex';
        });
        
        // Fermer le modal
        const closeButtons = uploadModal.querySelectorAll('.close-button, #cancel-upload');
        closeButtons.forEach(button => {
            button.addEventListener('click', function() {
                uploadModal.style.display = 'none';
            });
        });
        
        // Fermer en cliquant à l'extérieur
        uploadModal.addEventListener('click', function(e) {
            if (e.target === uploadModal) {
                uploadModal.style.display = 'none';
            }
        });
        
        // Gestion du formulaire d'upload
        const uploadForm = document.getElementById('upload-document-form');
        if (uploadForm) {
            uploadForm.addEventListener('submit', function(e) {
                e.preventDefault();
                uploadDocument(this);
            });
        }
    }
    
    // Modal de prévisualisation
    const previewModal = document.getElementById('preview-document-modal');
    if (previewModal) {
        // Fermer le modal
        const closeButtons = previewModal.querySelectorAll('.close-button, [data-close-modal]');
        closeButtons.forEach(button => {
            button.addEventListener('click', function() {
                previewModal.style.display = 'none';
            });
        });
        
        // Fermer en cliquant à l'extérieur
        previewModal.addEventListener('click', function(e) {
            if (e.target === previewModal) {
                previewModal.style.display = 'none';
            }
        });
    }
}

/**
 * Initialise les actions pour les documents (prévisualisation, suppression)
 */
function initDocumentActions() {
    // Boutons de prévisualisation
    const previewButtons = document.querySelectorAll('.preview-button');
    
    previewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const documentId = this.getAttribute('data-id');
            previewDocument(documentId);
        });
    });
    
    // Boutons de suppression
    const deleteButtons = document.querySelectorAll('.delete-button');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const documentId = this.getAttribute('data-id');
            deleteDocument(documentId);
        });
    });
}

/**
 * Téléverse un nouveau document
 * @param {HTMLFormElement} form - Formulaire d'upload
 */
async function uploadDocument(form) {
    // Créer un FormData avec les données du formulaire
    const formData = new FormData(form);
    
    try {
        // Afficher l'indicateur de chargement
        showLoading('Téléversement du document en cours...');
        
        // Appel API pour téléverser le document
        const response = await fetch('/api/documents/template/upload', {
            method: 'POST',
            body: formData
        });
        
        // Cacher l'indicateur de chargement
        hideLoading();
        
        if (!response.ok) {
            throw new Error('Erreur lors du téléversement du document');
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Fermer le modal
            const modal = document.getElementById('upload-document-modal');
            if (modal) modal.style.display = 'none';
            
            // Réinitialiser le formulaire
            form.reset();
            
            // Afficher un message de succès
            showAlert('success', 'Document téléversé avec succès');
            
            // Recharger la page pour afficher le nouveau document
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            showAlert('error', data.message || 'Erreur lors du téléversement du document');
        }
    } catch (error) {
        console.error('Erreur:', error);
        hideLoading();
        showAlert('error', 'Erreur lors du téléversement du document: ' + error.message);
    }
}

/**
 * Prévisualise un document
 * @param {String} documentId - ID du document
 */
async function previewDocument(documentId) {
    try {
        // Afficher l'indicateur de chargement
        showLoading('Chargement de la prévisualisation...');
        
        // Appel API pour obtenir les détails du document
        const response = await fetch(`/api/documents/template/${documentId}`);
        
        // Cacher l'indicateur de chargement
        hideLoading();
        
        if (!response.ok) {
            throw new Error('Erreur lors du chargement de la prévisualisation');
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Récupérer les références
            const modal = document.getElementById('preview-document-modal');
            const titleElem = document.getElementById('preview-document-title');
            const previewElem = document.getElementById('document-preview');
            const downloadLink = document.getElementById('preview-download-link');
            
            if (modal && titleElem && previewElem && downloadLink) {
                // Mettre à jour le contenu
                titleElem.textContent = data.data.name;
                downloadLink.href = data.data.url;
                downloadLink.download = data.data.fileName;
                
                // Mettre à jour la prévisualisation
                if (data.data.previewHtml) {
                    previewElem.innerHTML = data.data.previewHtml;
                } else {
                    // Afficher un message si la prévisualisation n'est pas disponible
                    previewElem.innerHTML = `
                        <div class="preview-not-available">
                            <div class="preview-icon">📄</div>
                            <p>La prévisualisation n'est pas disponible pour ce type de document.</p>
                            <p>Vous pouvez télécharger le document pour le consulter.</p>
                        </div>
                    `;
                }
                
                // Afficher le modal
                modal.style.display = 'flex';
            }
        } else {
            showAlert('error', data.message || 'Erreur lors du chargement de la prévisualisation');
        }
    } catch (error) {
        console.error('Erreur:', error);
        hideLoading();
        showAlert('error', 'Erreur lors du chargement de la prévisualisation: ' + error.message);
    }
}

/**
 * Supprime un document
 * @param {String} documentId - ID du document
 */
async function deleteDocument(documentId) {
    // Demander confirmation
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce document ?')) {
        return;
    }
    
    try {
        // Afficher l'indicateur de chargement
        showLoading('Suppression du document...');
        
        // Appel API pour supprimer le document
        const response = await fetch(`/api/documents/template/${documentId}`, {
            method: 'DELETE'
        });
        
        // Cacher l'indicateur de chargement
        hideLoading();
        
        if (!response.ok) {
            throw new Error('Erreur lors de la suppression du document');
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Afficher un message de succès
            showAlert('success', 'Document supprimé avec succès');
            
            // Supprimer la carte du document
            const documentCard = document.querySelector(`.document-card[data-id="${documentId}"]`);
            if (documentCard) {
                documentCard.style.animation = 'fadeOut 0.3s forwards';
                setTimeout(() => {
                    documentCard.parentNode.removeChild(documentCard);
                    
                    // Vérifier s'il reste des documents
                    const remainingCards = document.querySelectorAll('.document-card');
                    if (remainingCards.length === 0) {
                        // Aucun document restant, afficher l'état vide
                        const documentsGrid = document.querySelector('.documents-grid');
                        if (documentsGrid) {
                            documentsGrid.innerHTML = `
                                <div class="empty-state">
                                    <div class="empty-icon">📂</div>
                                    <p>Aucun document type disponible pour le moment.</p>
                                    <p>Cliquez sur "Ajouter un document" pour téléverser votre premier document type.</p>
                                </div>
                            `;
                        }
                    }
                }, 300);
            }
        } else {
            showAlert('error', data.message || 'Erreur lors de la suppression du document');
        }
    } catch (error) {
        console.error('Erreur:', error);
        hideLoading();
        showAlert('error', 'Erreur lors de la suppression du document: ' + error.message);
    }
}

// Exportation des fonctions pour une utilisation externe
window.documentsApp = {
    filterDocuments,
    uploadDocument,
    previewDocument,
    deleteDocument
};