/**
 * database.js - Gestion corrigée de la base de données d'entreprises
 */

// État global pour les entreprises
let allCompanies = [];
let filteredCompanies = [];
let currentPage = 1;
const itemsPerPage = 20;

document.addEventListener('DOMContentLoaded', function() {
    console.log("=== INITIALISATION DATABASE.JS ===");
    
    // Charger les entreprises
    loadCompanies();
    
    // Initialiser les événements
    initEventListeners();
});

/**
 * Charge les entreprises depuis l'API
 */
async function loadCompanies() {
    try {
        console.log("Chargement des entreprises...");
        showLoading('Chargement des entreprises...');
        
        const response = await fetch('/api/companies');
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            allCompanies = data.data || [];
            filteredCompanies = [...allCompanies];
            
            console.log(`${allCompanies.length} entreprises chargées`);
            
            renderCompanies();
            updatePaginationInfo();
            updateStats();
        } else {
            throw new Error(data.error || 'Erreur de chargement');
        }
    } catch (error) {
        console.error('Erreur chargement:', error);
        showAlert('error', `Erreur lors du chargement: ${error.message}`);
        
        // Afficher un état d'erreur
        const tableBody = document.getElementById('companies-table-body');
        if (tableBody) {
            tableBody.innerHTML = `
                <div class="error-state">
                    <div class="error-icon">❌</div>
                    <p>Erreur lors du chargement des entreprises</p>
                    <button class="button primary" onclick="loadCompanies()">Réessayer</button>
                </div>
            `;
        }
    } finally {
        hideLoading();
    }
}

/**
 * Met à jour les statistiques
 */
function updateStats() {
    // Statistiques par domaine
    const domainStats = {};
    allCompanies.forEach(company => {
        const domain = company.domain || 'Autre';
        domainStats[domain] = (domainStats[domain] || 0) + 1;
    });
    
    console.log("Statistiques par domaine:", domainStats);
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
                e.preventDefault();
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
    if (importModal) {
        const closeButtons = importModal.querySelectorAll('.close-button, #cancel-import');
        closeButtons.forEach(button => {
            button.addEventListener('click', () => closeModal('import-modal'));
        });
        
        const importForm = document.getElementById('import-form');
        if (importForm) {
            importForm.addEventListener('submit', handleImport);
        }
    }
    
    // Modal d'entreprise
    const companyModal = document.getElementById('company-modal');
    if (companyModal) {
        const closeButtons = companyModal.querySelectorAll('.close-button, #cancel-company');
        closeButtons.forEach(button => {
            button.addEventListener('click', () => closeModal('company-modal'));
        });
        
        const companyForm = document.getElementById('company-form');
        if (companyForm) {
            companyForm.addEventListener('submit', handleCompanySave);
        }
    }
    
    // Modal de détails
    const detailsModal = document.getElementById('company-details-modal');
    if (detailsModal) {
        const closeButtons = detailsModal.querySelectorAll('.close-button, #close-details-btn');
        closeButtons.forEach(button => {
            button.addEventListener('click', () => closeModal('company-details-modal'));
        });
        
        const editButton = document.getElementById('edit-from-details');
        if (editButton) {
            editButton.addEventListener('click', editFromDetailsModal);
        }
    }
    
    // Fermer modaux en cliquant à l'extérieur
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
    
    console.log("Filtrage:", { searchTerm, domainFilter, certificationFilter });
    
    filteredCompanies = allCompanies.filter(company => {
        // Filtre de recherche
        const matchesSearch = !searchTerm || 
            company.name.toLowerCase().includes(searchTerm) ||
            company.location.toLowerCase().includes(searchTerm) ||
            (company.domain && company.domain.toLowerCase().includes(searchTerm));
        
        // Filtre de domaine
        const matchesDomain = !domainFilter || company.domain === domainFilter;
        
        // Filtre de certification
        const matchesCertification = !certificationFilter || 
            (company.certifications && company.certifications.includes(certificationFilter));
        
        return matchesSearch && matchesDomain && matchesCertification;
    });
    
    console.log(`Filtrage: ${filteredCompanies.length}/${allCompanies.length} entreprises`);
    
    currentPage = 1;
    renderCompanies();
    updatePaginationInfo();
}

/**
 * Rend la liste des entreprises
 */
function renderCompanies() {
    const tableBody = document.getElementById('companies-table-body');
    if (!tableBody) {
        console.error("Élément companies-table-body non trouvé");
        return;
    }
    
    // Pagination
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const companiesToShow = filteredCompanies.slice(startIndex, endIndex);
    
    if (companiesToShow.length === 0) {
        tableBody.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <p>Aucune entreprise ne correspond à vos critères.</p>
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
                    ${company.contact?.email ? 
                        `<span class="company-email">${company.contact.email}</span>` : ''}
                </div>
            </div>
            <div class="company-domain">
                <span class="domain-badge ${getDomainClass(company.domain || 'Autre')}">
                    ${company.domain || 'Non spécifié'}
                </span>
            </div>
            <div class="company-location">${company.location || 'Non spécifié'}</div>
            <div class="company-certifications">
                ${(company.certifications || []).map(cert => 
                    `<span class="certification-badge">${cert}</span>`
                ).join('')}
            </div>
            <div class="company-ca">${company.ca || 'N/A'}</div>
            <div class="company-employees">${company.employees || 'N/A'}</div>
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
        const startIndex = Math.min((currentPage - 1) * itemsPerPage + 1, filteredCompanies.length);
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
    const searchInput = document.getElementById('company-search');
    const domainFilter = document.getElementById('domain-filter');
    const certificationFilter = document.getElementById('certification-filter');
    
    if (searchInput) searchInput.value = '';
    if (domainFilter) domainFilter.value = '';
    if (certificationFilter) certificationFilter.value = '';
    
    filteredCompanies = [...allCompanies];
    currentPage = 1;
    renderCompanies();
    updatePaginationInfo();
}

/**
 * Ouvre le modal d'import
 */
function openImportModal() {
    const modal = document.getElementById('import-modal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

/**
 * Ouvre le modal d'ajout d'entreprise
 */
function openAddCompanyModal() {
    resetCompanyForm();
    const modalTitle = document.getElementById('company-modal-title');
    const modal = document.getElementById('company-modal');
    
    if (modalTitle) modalTitle.textContent = 'Ajouter une entreprise';
    if (modal) modal.style.display = 'flex';
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
            loadCompanies(); // Recharger
        } else {
            showAlert('error', data.message || 'Erreur lors de l\'import');
        }
    } catch (error) {
        console.error('Erreur import:', error);
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
    
    // Extraire les données
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
    
    // Gérer le contact
    if (companyData.email || companyData.phone) {
        companyData.contact = {};
        if (companyData.email) companyData.contact.email = companyData.email;
        if (companyData.phone) companyData.contact.phone = companyData.phone;
        delete companyData.email;
        delete companyData.phone;
    }
    
    try {
        showLoading('Sauvegarde...');
        
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
            loadCompanies();
        } else {
            showAlert('error', data.message || 'Erreur lors de la sauvegarde');
        }
    } catch (error) {
        console.error('Erreur sauvegarde:', error);
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
    if (!company) {
        showAlert('error', 'Entreprise non trouvée');
        return;
    }
    
    const detailsContent = document.getElementById('company-details-content');
    const detailsTitle = document.getElementById('company-details-title');
    
    if (detailsTitle) detailsTitle.textContent = company.name;
    
    if (detailsContent) {
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
                            <span class="domain-badge ${getDomainClass(company.domain || 'Autre')}">
                                ${company.domain || 'Non spécifié'}
                            </span>
                        </span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Localisation :</span>
                        <span class="detail-value">${company.location || 'Non spécifié'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">CA :</span>
                        <span class="detail-value">${company.ca || 'Non spécifié'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Effectifs :</span>
                        <span class="detail-value">${company.employees || 'Non spécifié'}</span>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h4>Certifications</h4>
                    <div class="certifications-list">
                        ${(company.certifications || []).length > 0 ? 
                            (company.certifications || []).map(cert => 
                                `<span class="certification-badge">${cert}</span>`
                            ).join('') : 
                            '<span class="text-muted">Aucune certification</span>'
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
                        <h4>Expérience</h4>
                        <div class="detail-item">
                            <span class="detail-value">${company.experience}</span>
                        </div>
                    </div>
                ` : ''}
                
                ${company.lots_marches && company.lots_marches.length > 0 ? `
                    <div class="detail-section">
                        <h4>Historique des marchés</h4>
                        ${company.lots_marches.map(lot => `
                            <div class="detail-item">
                                <span class="detail-label">${lot.type || 'Marché'} :</span>
                                <span class="detail-value">${lot.description || 'Pas de description'}</span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    // Stocker l'ID pour l'édition
    const editButton = document.getElementById('edit-from-details');
    if (editButton) {
        editButton.setAttribute('data-company-id', companyId);
    }
    
    const modal = document.getElementById('company-details-modal');
    if (modal) modal.style.display = 'flex';
}

/**
 * Édite une entreprise depuis le modal de détails
 */
function editFromDetailsModal() {
    const editButton = document.getElementById('edit-from-details');
    const companyId = editButton?.getAttribute('data-company-id');
    
    if (companyId) {
        closeModal('company-details-modal');
        editCompany(companyId);
    }
}

/**
 * Édite une entreprise
 */
function editCompany(companyId) {
    const company = allCompanies.find(c => c.id === companyId);
    if (!company) {
        showAlert('error', 'Entreprise non trouvée');
        return;
    }
    
    // Remplir le formulaire
    const form = document.getElementById('company-form');
    if (form) {
        form.querySelector('#company-id').value = company.id;
        form.querySelector('#company-name-input').value = company.name;
        form.querySelector('#company-domain-input').value = company.domain || '';
        form.querySelector('#company-location-input').value = company.location || '';
        form.querySelector('#company-ca-input').value = company.ca || '';
        form.querySelector('#company-employees-input').value = company.employees || '';
        
        if (company.contact) {
            if (company.contact.email) {
                form.querySelector('#company-email').value = company.contact.email;
            }
            if (company.contact.phone) {
                form.querySelector('#company-phone').value = company.contact.phone;
            }
        }
        
        if (company.experience) {
            form.querySelector('#company-experience').value = company.experience;
        }
        
        // Certifications
        const certCheckboxes = form.querySelectorAll('input[name="certifications"]');
        certCheckboxes.forEach(checkbox => {
            checkbox.checked = (company.certifications || []).includes(checkbox.value);
        });
    }
    
    const modalTitle = document.getElementById('company-modal-title');
    const modal = document.getElementById('company-modal');
    
    if (modalTitle) modalTitle.textContent = 'Modifier l\'entreprise';
    if (modal) modal.style.display = 'flex';
}

/**
 * Supprime une entreprise
 */
async function deleteCompany(companyId) {
    const company = allCompanies.find(c => c.id === companyId);
    if (!company) {
        showAlert('error', 'Entreprise non trouvée');
        return;
    }
    
    if (!confirm(`Êtes-vous sûr de vouloir supprimer "${company.name}" ?`)) {
        return;
    }
    
    try {
        showLoading('Suppression...');
        
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
            loadCompanies();
        } else {
            showAlert('error', data.message || 'Erreur lors de la suppression');
        }
    } catch (error) {
        console.error('Erreur suppression:', error);
        showAlert('error', 'Erreur lors de la suppression');
    } finally {
        hideLoading();
    }
}

/**
 * Ferme un modal
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Remet à zéro le formulaire
 */
function resetCompanyForm() {
    const form = document.getElementById('company-form');
    if (form) {
        form.reset();
        form.querySelector('#company-id').value = '';
    }
}

/**
 * Fonction de debounce
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

// Exposer les fonctions globalement
window.viewCompanyDetails = viewCompanyDetails;
window.editCompany = editCompany;
window.deleteCompany = deleteCompany;
window.clearFilters = clearFilters;

console.log("=== DATABASE.JS INITIALISÉ ===");