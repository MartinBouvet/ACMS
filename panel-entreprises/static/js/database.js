/**
 * database.js - Gestion améliorée de la base de données d'entreprises
 */

// État global pour les entreprises
let allCompanies = [];
let filteredCompanies = [];
let currentPage = 1;
const itemsPerPage = 20;

document.addEventListener('DOMContentLoaded', function() {
    // Charger les entreprises initiales
    loadCompanies();
    
    // Initialiser les événements
    initEventListeners();
});

/**
 * Charge les entreprises depuis l'API
 */
async function loadCompanies() {
    try {
        showLoading('Chargement des entreprises...');
        
        const response = await fetch('/api/companies');
        const data = await response.json();
        
        if (data.success) {
            allCompanies = data.data;
            filteredCompanies = [...allCompanies];
            renderCompanies();
            updatePaginationInfo();
        } else {
            showAlert('error', 'Erreur lors du chargement des entreprises');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showAlert('error', 'Erreur de connexion');
    } finally {
        hideLoading();
    }
}

/**
 * Initialise tous les écouteurs d'événements
 */
function initEventListeners() {
    // Recherche
    const searchInput = document.getElementById('company-search');
    const searchButton = document.getElementById('search-button');
    
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterCompanies, 300));
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                filterCompanies();
            }
        });
    }
    
    if (searchButton) {
        searchButton.addEventListener('click', filterCompanies);
    }
    
    // Filtres
    const domainFilter = document.getElementById('domain-filter');
    const certificationFilter = document.getElementById('certification-filter');
    
    if (domainFilter) {
        domainFilter.addEventListener('change', filterCompanies);
    }
    
    if (certificationFilter) {
        certificationFilter.addEventListener('change', filterCompanies);
    }
    
    // Boutons d'action
    const importButton = document.getElementById('import-button');
    const addCompanyButton = document.getElementById('add-company-button');
    
    if (importButton) {
        importButton.addEventListener('click', openImportModal);
    }
    
    if (addCompanyButton) {
        addCompanyButton.addEventListener('click', openAddCompanyModal);
    }
    
    // Modaux
    initModalEventListeners();
}

/**
 * Initialise les écouteurs pour les modaux
 */
function initModalEventListeners() {
    // Modal d'import
    const importModal = document.getElementById('import-modal');
    const closeImportModal = document.getElementById('close-import-modal');
    const cancelImport = document.getElementById('cancel-import');
    const importForm = document.getElementById('import-form');
    
    if (closeImportModal) {
        closeImportModal.addEventListener('click', () => closeModal('import-modal'));
    }
    
    if (cancelImport) {
        cancelImport.addEventListener('click', () => closeModal('import-modal'));
    }
    
    if (importForm) {
        importForm.addEventListener('submit', handleImport);
    }
    
    // Modal d'entreprise
    const companyModal = document.getElementById('company-modal');
    const closeCompanyModal = document.getElementById('close-company-modal');
    const cancelCompany = document.getElementById('cancel-company');
    const companyForm = document.getElementById('company-form');
    
    if (closeCompanyModal) {
        closeCompanyModal.addEventListener('click', () => closeModal('company-modal'));
    }
    
    if (cancelCompany) {
        cancelCompany.addEventListener('click', () => closeModal('company-modal'));
    }
    
    if (companyForm) {
        companyForm.addEventListener('submit', handleCompanySave);
    }
    
    // Modal de détails
    const detailsModal = document.getElementById('company-details-modal');
    const closeDetailsModal = document.getElementById('close-details-modal');
    const closeDetailsBtn = document.getElementById('close-details-btn');
    const editFromDetails = document.getElementById('edit-from-details');
    
    if (closeDetailsModal) {
        closeDetailsModal.addEventListener('click', () => closeModal('company-details-modal'));
    }
    
    if (closeDetailsBtn) {
        closeDetailsBtn.addEventListener('click', () => closeModal('company-details-modal'));
    }
    
    if (editFromDetails) {
        editFromDetails.addEventListener('click', editFromDetailsModal);
    }
    
    // Fermer les modaux en cliquant à l'extérieur
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });
}

/**
 * Filtre les entreprises selon les critères
 */
function filterCompanies() {
    const searchTerm = document.getElementById('company-search')?.value.toLowerCase() || '';
    const domainFilter = document.getElementById('domain-filter')?.value || '';
    const certificationFilter = document.getElementById('certification-filter')?.value || '';
    
    filteredCompanies = allCompanies.filter(company => {
        // Filtre de recherche textuelle
        const matchesSearch = !searchTerm || 
            company.name.toLowerCase().includes(searchTerm) ||
            company.location.toLowerCase().includes(searchTerm) ||
            company.domain.toLowerCase().includes(searchTerm);
        
        // Filtre de domaine
        const matchesDomain = !domainFilter || company.domain === domainFilter;
        
        // Filtre de certification
        const matchesCertification = !certificationFilter || 
            (company.certifications && company.certifications.includes(certificationFilter));
        
        return matchesSearch && matchesDomain && matchesCertification;
    });
    
    currentPage = 1;
    renderCompanies();
    updatePaginationInfo();
}

/**
 * Rend la liste des entreprises
 */
function renderCompanies() {
    const tableBody = document.getElementById('companies-table-body');
    if (!tableBody) return;
    
    // Calculer les éléments à afficher pour la pagination
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const companiesToShow = filteredCompanies.slice(startIndex, endIndex);
    
    if (companiesToShow.length === 0) {
        tableBody.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <p>Aucune entreprise ne correspond à vos critères de recherche.</p>
                <button class="button secondary" onclick="clearFilters()">Effacer les filtres</button>
            </div>
        `;
        return;
    }
    
    const html = companiesToShow.map(company => `
        <div class="table-row" data-company-id="${company.id}">
            <div class="company-name">
                <div class="company-main-info">
                    <span class="company-title">${company.name}</span>
                    ${company.contact && company.contact.email ? 
                        `<span class="company-email">${company.contact.email}</span>` : ''}
                </div>
            </div>
            <div class="company-domain">
                <span class="domain-badge ${getDomainClass(company.domain)}">${company.domain}</span>
            </div>
            <div class="company-location">${company.location}</div>
            <div class="company-certifications">
                ${company.certifications.map(cert => 
                    `<span class="certification-badge">${cert}</span>`
                ).join('')}
            </div>
            <div class="company-ca">${company.ca}</div>
            <div class="company-employees">${company.employees}</div>
            <div class="company-actions">
                <button class="action-button view-button" onclick="viewCompanyDetails('${company.id}')" title="Voir détails">👁️</button>
                <button class="action-button edit-button" onclick="editCompany('${company.id}')" title="Modifier">✏️</button>
                <button class="action-button delete-button" onclick="deleteCompany('${company.id}')" title="Supprimer">🗑️</button>
            </div>
        </div>
    `).join('');
    
    tableBody.innerHTML = html;
}

/**
 * Retourne la classe CSS pour un domaine
 */
function getDomainClass(domain) {
    const domainClasses = {
        'Électricité': 'domain-electricity',
        'Mécanique': 'domain-mechanical',
        'Hydraulique': 'domain-hydraulic',
        'Bâtiment': 'domain-construction',
        'Maintenance': 'domain-maintenance'
    };
    return domainClasses[domain] || 'domain-other';
}

/**
 * Met à jour les informations de pagination
 */
function updatePaginationInfo() {
    const paginationInfo = document.getElementById('pagination-info');
    const currentPageBtn = document.getElementById('current-page');
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    
    if (paginationInfo) {
        const startIndex = (currentPage - 1) * itemsPerPage + 1;
        const endIndex = Math.min(currentPage * itemsPerPage, filteredCompanies.length);
        paginationInfo.textContent = `Affichage de ${startIndex}-${endIndex} sur ${filteredCompanies.length} entreprises`;
    }
    
    if (currentPageBtn) {
        currentPageBtn.textContent = currentPage;
    }
    
    if (prevPageBtn) {
        prevPageBtn.disabled = currentPage <= 1;
        prevPageBtn.onclick = () => changePage(currentPage - 1);
    }
    
    if (nextPageBtn) {
        const totalPages = Math.ceil(filteredCompanies.length / itemsPerPage);
        nextPageBtn.disabled = currentPage >= totalPages;
        nextPageBtn.onclick = () => changePage(currentPage + 1);
    }
}

/**
 * Change de page
 */
function changePage(newPage) {
    const totalPages = Math.ceil(filteredCompanies.length / itemsPerPage);
    if (newPage >= 1 && newPage <= totalPages) {
        currentPage = newPage;
        renderCompanies();
        updatePaginationInfo();
    }
}

/**
 * Efface tous les filtres
 */
function clearFilters() {
    document.getElementById('company-search').value = '';
    document.getElementById('domain-filter').value = '';
    document.getElementById('certification-filter').value = '';
    filteredCompanies = [...allCompanies];
    currentPage = 1;
    renderCompanies();
    updatePaginationInfo();
}

/**
 * Ouvre le modal d'import
 */
function openImportModal() {
    document.getElementById('import-modal').style.display = 'flex';
}

/**
 * Ouvre le modal d'ajout d'entreprise
 */
function openAddCompanyModal() {
    resetCompanyForm();
    document.getElementById('company-modal-title').textContent = 'Ajouter une entreprise';
    document.getElementById('company-modal').style.display = 'flex';
}

/**
 * Gère l'import de fichier Excel
 */
async function handleImport(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const file = formData.get('file');
    
    if (!file) {
        showAlert('error', 'Veuillez sélectionner un fichier');
        return;
    }
    
    try {
        showLoading('Import en cours...');
        
        const response = await fetch('/api/database/import-excel', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('success', `${data.imported} entreprises importées avec succès`);
            closeModal('import-modal');
            loadCompanies(); // Recharger les données
        } else {
            showAlert('error', data.message || 'Erreur lors de l\'import');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showAlert('error', 'Erreur lors de l\'import du fichier');
    } finally {
        hideLoading();
    }
}

/**
 * Gère la sauvegarde d'une entreprise
 */
async function handleCompanySave(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const companyData = {};
    
    // Extraire les données du formulaire
    for (const [key, value] of formData.entries()) {
        if (key === 'certifications') {
            if (!companyData.certifications) {
                companyData.certifications = [];
            }
            companyData.certifications.push(value);
        } else {
            companyData[key] = value;
        }
    }
    
    // Gérer les informations de contact
    if (companyData.email || companyData.phone) {
        companyData.contact = {};
        if (companyData.email) companyData.contact.email = companyData.email;
        if (companyData.phone) companyData.contact.phone = companyData.phone;
        delete companyData.email;
        delete companyData.phone;
    }
    
    try {
        showLoading('Sauvegarde en cours...');
        
        const url = companyData.id ? '/api/database/update-company' : '/api/database/add-company';
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(companyData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            const action = companyData.id ? 'modifiée' : 'ajoutée';
            showAlert('success', `Entreprise ${action} avec succès`);
            closeModal('company-modal');
            loadCompanies(); // Recharger les données
        } else {
            showAlert('error', data.message || 'Erreur lors de la sauvegarde');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showAlert('error', 'Erreur lors de la sauvegarde');
    } finally {
        hideLoading();
    }
}

/**
 * Affiche les détails d'une entreprise
 */
function viewCompanyDetails(companyId) {
    const company = allCompanies.find(c => c.id === companyId);
    if (!company) return;
    
    const detailsContent = document.getElementById('company-details-content');
    const detailsTitle = document.getElementById('company-details-title');
    
    detailsTitle.textContent = company.name;
    
    detailsContent.innerHTML = `
        <div class="company-details-grid">
            <div class="detail-section">
                <h4>Informations générales</h4>
                <div class="detail-item">
                    <span class="detail-label">Nom :</span>
                    <span class="detail-value">${company.name}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Domaine :</span>
                    <span class="detail-value">
                        <span class="domain-badge ${getDomainClass(company.domain)}">${company.domain}</span>
                    </span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Localisation :</span>
                    <span class="detail-value">${company.location}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Chiffre d'affaires :</span>
                    <span class="detail-value">${company.ca}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Effectifs :</span>
                    <span class="detail-value">${company.employees}</span>
                </div>
            </div>
            
            <div class="detail-section">
                <h4>Certifications</h4>
                <div class="certifications-list">
                    ${company.certifications.length > 0 ? 
                        company.certifications.map(cert => 
                            `<span class="certification-badge">${cert}</span>`
                        ).join('') : 
                        '<span class="text-muted">Aucune certification renseignée</span>'
                    }
                </div>
            </div>
            
            ${company.contact ? `
                <div class="detail-section">
                    <h4>Contact</h4>
                    ${company.contact.email ? `
                        <div class="detail-item">
                            <span class="detail-label">Email :</span>
                            <span class="detail-value">
                                <a href="mailto:${company.contact.email}">${company.contact.email}</a>
                            </span>
                        </div>
                    ` : ''}
                    ${company.contact.phone ? `
                        <div class="detail-item">
                            <span class="detail-label">Téléphone :</span>
                            <span class="detail-value">
                                <a href="tel:${company.contact.phone}">${company.contact.phone}</a>
                            </span>
                        </div>
                    ` : ''}
                </div>
            ` : ''}
            
            ${company.experience && company.experience !== 'Non spécifié' ? `
                <div class="detail-section">
                    <h4>Expérience / Références</h4>
                    <div class="detail-item">
                        <span class="detail-value">${company.experience}</span>
                    </div>
                </div>
            ` : ''}
        </div>
    `;
    
    // Stocker l'ID pour l'édition
    document.getElementById('edit-from-details').setAttribute('data-company-id', companyId);
    
    document.getElementById('company-details-modal').style.display = 'flex';
}

/**
 * Édite une entreprise depuis le modal de détails
 */
function editFromDetailsModal() {
    const companyId = document.getElementById('edit-from-details').getAttribute('data-company-id');
    closeModal('company-details-modal');
    editCompany(companyId);
}

/**
 * Édite une entreprise
 */
function editCompany(companyId) {
    const company = allCompanies.find(c => c.id === companyId);
    if (!company) return;
    
    // Remplir le formulaire avec les données existantes
    document.getElementById('company-id').value = company.id;
    document.getElementById('company-name-input').value = company.name;
    document.getElementById('company-domain-input').value = company.domain;
    document.getElementById('company-location-input').value = company.location;
    document.getElementById('company-ca-input').value = company.ca;
    document.getElementById('company-employees-input').value = company.employees;
    
    if (company.contact) {
        if (company.contact.email) {
            document.getElementById('company-email').value = company.contact.email;
        }
        if (company.contact.phone) {
            document.getElementById('company-phone').value = company.contact.phone;
        }
    }
    
    if (company.experience) {
        document.getElementById('company-experience').value = company.experience;
    }
    
    // Cocher les certifications
    const certCheckboxes = document.querySelectorAll('input[name="certifications"]');
    certCheckboxes.forEach(checkbox => {
        checkbox.checked = company.certifications.includes(checkbox.value);
    });
    
    document.getElementById('company-modal-title').textContent = 'Modifier l\'entreprise';
    document.getElementById('company-modal').style.display = 'flex';
}

/**
 * Supprime une entreprise
 */
async function deleteCompany(companyId) {
    const company = allCompanies.find(c => c.id === companyId);
    if (!company) return;
    
    if (!confirm(`Êtes-vous sûr de vouloir supprimer l'entreprise "${company.name}" ?`)) {
        return;
    }
    
    try {
        showLoading('Suppression en cours...');
        
        const response = await fetch('/api/database/delete-company', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: companyId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('success', 'Entreprise supprimée avec succès');
            loadCompanies(); // Recharger les données
        } else {
            showAlert('error', data.message || 'Erreur lors de la suppression');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showAlert('error', 'Erreur lors de la suppression');
    } finally {
        hideLoading();
    }
}

/**
 * Ferme un modal
 */
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

/**
 * Remet à zéro le formulaire d'entreprise
 */
function resetCompanyForm() {
    document.getElementById('company-form').reset();
    document.getElementById('company-id').value = '';
}

/**
 * Fonction de debounce pour éviter trop de requêtes
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Exposer les fonctions globalement pour les onclick
window.viewCompanyDetails = viewCompanyDetails;
window.editCompany = editCompany;
window.deleteCompany = deleteCompany;
window.clearFilters = clearFilters;