// static/js/search.js - Version complète et corrigée
document.addEventListener('DOMContentLoaded', function() {
    console.log("=== INITIALISATION SEARCH.JS ===");
    
    // État global de l'application
    const state = {
        currentStep: 1,
        cahierDesCharges: null,
        cahierDesChargesText: '',
        keywords: [],
        selectionCriteria: [],
        attributionCriteria: [],
        matchedCompanies: [],
        selectedCompanies: [],
        projectData: {
            title: '',
            description: ''
        },
        isProcessing: false  // Flag pour éviter les appels multiples
    };

    // Références aux éléments DOM
    const stepIndicator = document.querySelector('.step-indicator');
    const stepContent = document.getElementById('step-content');
    const fileDropzone = document.getElementById('file-dropzone');
    const fileInput = document.getElementById('file-input');
    const browseButton = document.getElementById('browse-button');

    console.log("Éléments DOM trouvés:", {
        stepIndicator: !!stepIndicator,
        stepContent: !!stepContent,
        fileDropzone: !!fileDropzone,
        fileInput: !!fileInput,
        browseButton: !!browseButton
    });

    // Initialisation
    initializeEventListeners();

    function initializeEventListeners() {
        console.log("Initialisation des écouteurs d'événements");
        
        if (fileDropzone && fileInput && browseButton) {
            initFileUploadListeners();
        }
    }

    function initFileUploadListeners() {
        console.log("Initialisation des écouteurs de fichiers");
        
        // Clic sur le dropzone
        fileDropzone.addEventListener('click', function() {
            console.log("Clic sur dropzone");
            fileInput.click();
        });

        // Clic sur le bouton "Parcourir"
        browseButton.addEventListener('click', function(e) {
            e.preventDefault();
            console.log("Clic sur bouton parcourir");
            fileInput.click();
        });

        // Sélection d'un fichier
        fileInput.addEventListener('change', function(e) {
            console.log("Fichier sélectionné", e.target.files);
            if (e.target.files.length > 0) {
                handleFileSelected(e.target.files[0]);
            }
        });

        // Drag and drop
        fileDropzone.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
            fileDropzone.classList.add('dragging');
        });

        fileDropzone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            fileDropzone.classList.remove('dragging');
        });

        fileDropzone.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            fileDropzone.classList.remove('dragging');
            console.log("Fichier déposé", e.dataTransfer.files);

            if (e.dataTransfer.files.length > 0) {
                handleFileSelected(e.dataTransfer.files[0]);
            }
        });
    }

    function handleFileSelected(file) {
        console.log("=== TRAITEMENT FICHIER ===");
        console.log("Fichier:", file.name, file.type, file.size);
        
        // Vérifier si un traitement est déjà en cours
        if (state.isProcessing) {
            console.log("Traitement déjà en cours, abandon");
            showAlert('warning', 'Un traitement est déjà en cours. Veuillez patienter.');
            return;
        }

        // Validation du fichier
        const allowedTypes = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'text/plain'
        ];
        const maxSize = 10 * 1024 * 1024; // 10 MB

        if (!allowedTypes.includes(file.type)) {
            showAlert('error', 'Type de fichier non supporté. Utilisez PDF, DOC, DOCX ou TXT.');
            return;
        }

        if (file.size > maxSize) {
            showAlert('error', 'Fichier trop volumineux. Maximum 10 MB.');
            return;
        }

        // Marquer le traitement comme en cours
        state.isProcessing = true;

        // Mettre à jour l'UI
        updateDropzoneForProcessing(file.name);

        // Traiter le fichier
        processFileUpload(file);
    }

    function updateDropzoneForProcessing(fileName) {
        fileDropzone.innerHTML = `
            <div class="dropzone-content uploading">
                <div class="spinner"></div>
                <p>Analyse en cours...</p>
                <p class="file-name">${fileName}</p>
            </div>
        `;
    }

    async function processFileUpload(file) {
        try {
            console.log("=== ÉTAPE 1: UPLOAD FICHIER ===");
            
            // 1. Uploader et parser le document
            const parseResult = await uploadAndParseDocument(file);
            if (!parseResult.success) {
                throw new Error(parseResult.message);
            }

            console.log("Document parsé avec succès");
            state.cahierDesCharges = file;
            state.cahierDesChargesText = parseResult.data.text;

            console.log("=== ÉTAPE 2: ANALYSE IA ===");
            
            // 2. Analyser le document avec l'IA
            const analysisResult = await analyzeDocumentWithAI();
            if (!analysisResult.success) {
                throw new Error(analysisResult.message);
            }

            console.log("Analyse IA réussie");
            state.keywords = analysisResult.data.keywords || [];
            state.selectionCriteria = analysisResult.data.selectionCriteria || [];
            state.attributionCriteria = analysisResult.data.attributionCriteria || [];

            console.log("Résultats:", {
                keywords: state.keywords.length,
                selectionCriteria: state.selectionCriteria.length,
                attributionCriteria: state.attributionCriteria.length
            });

            // 3. Passer à l'étape suivante
            goToStep(2);

        } catch (error) {
            console.error("Erreur traitement:", error);
            showErrorInDropzone(error.message);
        } finally {
            // Libérer le flag de traitement
            state.isProcessing = false;
        }
    }

    async function uploadAndParseDocument(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/files/parse-document', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error("Erreur upload:", error);
            return {
                success: false,
                message: `Erreur lors du téléversement: ${error.message}`
            };
        }
    }

    async function analyzeDocumentWithAI() {
        try {
            const response = await fetch('/api/ia/analyze-document', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    documentText: state.cahierDesChargesText 
                })
            });

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error("Erreur analyse IA:", error);
            return {
                success: false,
                message: `Erreur lors de l'analyse: ${error.message}`
            };
        }
    }

    function showErrorInDropzone(errorMessage) {
        fileDropzone.innerHTML = `
            <div class="dropzone-content error">
                <div class="error-icon">❌</div>
                <p>Erreur: ${errorMessage}</p>
                <button class="button secondary" onclick="location.reload()">Réessayer</button>
            </div>
        `;
    }

    function goToStep(step) {
        console.log(`=== PASSAGE À L'ÉTAPE ${step} ===`);
        
        if (step < 1 || step > 4) {
            console.error("Étape invalide:", step);
            return;
        }

        state.currentStep = step;
        updateStepIndicator(step);
        renderStepContent(step);
    }

    function updateStepIndicator(currentStep) {
        const steps = stepIndicator.querySelectorAll('.step');
        const connectors = stepIndicator.querySelectorAll('.step-connector');

        steps.forEach((step, index) => {
            const stepNumber = index + 1;
            const stepNumberElement = step.querySelector('.step-number');
            
            if (stepNumber < currentStep) {
                step.classList.remove('active');
                step.classList.add('completed');
                stepNumberElement.innerHTML = '✓';
            } else if (stepNumber === currentStep) {
                step.classList.add('active');
                step.classList.remove('completed');
                stepNumberElement.innerHTML = stepNumber;
            } else {
                step.classList.remove('active', 'completed');
                stepNumberElement.innerHTML = stepNumber;
            }
        });

        connectors.forEach((connector, index) => {
            if (index < currentStep - 1) {
                connector.classList.add('completed');
            } else {
                connector.classList.remove('completed');
            }
        });
    }

    function renderStepContent(step) {
        console.log(`Rendu de l'étape ${step}`);
        
        // Supprimer les anciens panneaux actifs
        const activePanels = document.querySelectorAll('.step-panel.active');
        activePanels.forEach(panel => {
            panel.classList.remove('active');
        });

        // Chercher ou créer le panneau pour cette étape
        let panel = document.querySelector(`.step-panel[data-step="${step}"]`);
        
        if (!panel) {
            panel = document.createElement('div');
            panel.className = 'step-panel';
            panel.setAttribute('data-step', step);
            stepContent.appendChild(panel);
        }

        // Remplir le contenu selon l'étape
        switch (step) {
            case 1:
                // Étape 1 déjà dans le HTML
                break;
                
            case 2:
                renderStep2Content(panel);
                break;
                
            case 3:
                renderStep3Content(panel);
                break;
                
            case 4:
                renderStep4Content(panel);
                break;
        }

        panel.classList.add('active');
    }

    function renderStep2Content(panel) {
        panel.innerHTML = `
            <h2>2. Critères extraits par l'IA</h2>
            
            <div class="keywords-section">
                <h3>Mots-clés identifiés</h3>
                <div class="keywords-container">
                    ${state.keywords.map(keyword => `<span class="keyword-tag">${keyword}</span>`).join('')}
                </div>
            </div>
            
            <div class="criteria-section">
                <h3>Critères de sélection</h3>
                <p>Critères extraits automatiquement du cahier des charges :</p>
                <div class="selection-criteria">
                    ${renderSelectionCriteria()}
                </div>
            </div>
            
            <div class="criteria-section">
                <h3>Critères d'attribution</h3>
                <p>Répartition proposée pour l'évaluation des offres :</p>
                <div class="attribution-criteria">
                    ${renderAttributionCriteria()}
                </div>
            </div>
            
            <div class="step-navigation">
                <button class="button secondary" onclick="window.searchApp.goToStep(1)">Retour</button>
                <button class="button primary" onclick="window.searchApp.findMatchingCompanies()">Rechercher les entreprises</button>
            </div>
        `;
    }

    function renderSelectionCriteria() {
        if (!state.selectionCriteria || state.selectionCriteria.length === 0) {
            return '<p class="empty-state">Aucun critère trouvé</p>';
        }

        return state.selectionCriteria.map(criterion => `
            <div class="criterion-card" data-id="${criterion.id}">
                <div class="criterion-header">
                    <div class="criterion-info">
                        <h4>${criterion.name}</h4>
                        <p>${criterion.description || ''}</p>
                    </div>
                    <div class="criterion-toggle">
                        <label class="toggle-switch">
                            <input type="checkbox" ${criterion.selected ? 'checked' : ''} 
                                   onchange="window.searchApp.toggleSelectionCriterion(${criterion.id}, this.checked)">
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                </div>
            </div>
        `).join('');
    }

    function renderAttributionCriteria() {
        if (!state.attributionCriteria || state.attributionCriteria.length === 0) {
            return '<p class="empty-state">Aucun critère trouvé</p>';
        }

        const totalWeight = state.attributionCriteria.reduce((sum, criterion) => sum + criterion.weight, 0);
        const isValid = totalWeight === 100;

        return `
            <div class="attribution-total ${isValid ? 'valid' : 'invalid'}">
                <span>Total: ${totalWeight}%</span>
                ${isValid ? '<span class="valid-icon">✓</span>' : '<span class="invalid-icon">⚠️</span>'}
            </div>
            
            <div class="attribution-criteria-list">
                ${state.attributionCriteria.map(criterion => `
                    <div class="attribution-criterion" data-id="${criterion.id}">
                        <div class="criterion-name">${criterion.name}</div>
                        <div class="criterion-weight">
                            <input type="range" min="0" max="100" step="5" value="${criterion.weight}"
                                   onchange="window.searchApp.updateAttributionWeight(${criterion.id}, this.value)"
                                   oninput="window.searchApp.updateWeightDisplay(${criterion.id}, this.value)">
                            <span class="weight-value">${criterion.weight}%</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    async function findMatchingCompanies() {
        console.log("=== RECHERCHE ENTREPRISES ===");
        
        // Vérifier si un traitement est en cours
        if (state.isProcessing) {
            console.log("Recherche déjà en cours");
            return;
        }

        state.isProcessing = true;
        
        try {
            // Afficher le chargement
            showLoading('Recherche des entreprises correspondantes...');

            // Préparer les critères sélectionnés
            const selectedCriteria = state.selectionCriteria.filter(c => c.selected);
            console.log("Critères sélectionnés:", selectedCriteria);

            // Appeler l'API
            const response = await fetch('/api/ia/find-matching-companies', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    criteria: selectedCriteria
                })
            });

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.message || 'Erreur lors de la recherche');
            }

            // Stocker les résultats
            state.matchedCompanies = data.data || [];
            state.selectedCompanies = state.matchedCompanies.map(company => ({
                ...company,
                selected: true
            }));

            console.log(`${state.matchedCompanies.length} entreprises trouvées`);

            // Passer à l'étape suivante
            goToStep(3);

        } catch (error) {
            console.error("Erreur recherche:", error);
            showAlert('error', error.message);
        } finally {
            hideLoading();
            state.isProcessing = false;
        }
    }

    function renderStep3Content(panel) {
        panel.innerHTML = `
            <h2>3. Entreprises correspondantes</h2>
            
            <div class="companies-result">
                <h3>Résultats de la recherche</h3>
                <p>L'IA a identifié ${state.matchedCompanies.length} entreprises correspondant à vos critères :</p>
                
                <div class="companies-list">
                    ${renderCompaniesTable()}
                </div>
                
                <div class="companies-actions">
                    <div class="selected-info">
                        <span class="selected-count">
                            ${state.selectedCompanies.filter(c => c.selected).length} entreprises sélectionnées
                        </span>
                    </div>
                    <div class="action-buttons">
                        <button class="button secondary" onclick="window.searchApp.addCompanyManually()">
                            Ajouter manuellement
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="step-navigation">
                <button class="button secondary" onclick="window.searchApp.goToStep(2)">Retour</button>
                <button class="button primary" onclick="window.searchApp.goToStep(4)">Générer les documents</button>
            </div>
        `;
    }

    function renderCompaniesTable() {
        if (!state.matchedCompanies || state.matchedCompanies.length === 0) {
            return '<p class="empty-state">Aucune entreprise trouvée correspondant à vos critères</p>';
        }

        return `
            <table class="companies-table">
                <thead>
                    <tr>
                        <th>Sélection</th>
                        <th>Entreprise</th>
                        <th>Domaine</th>
                        <th>Localisation</th>
                        <th>Certifications</th>
                        <th>Score</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${state.matchedCompanies.map(company => `
                        <tr class="company-row ${company.selected ? 'selected' : ''}" data-id="${company.id}">
                            <td>
                                <label class="checkbox">
                                    <input type="checkbox" ${company.selected ? 'checked' : ''} 
                                           onchange="window.searchApp.toggleCompanySelection('${company.id}', this.checked)">
                                    <span class="checkmark"></span>
                                </label>
                            </td>
                            <td>
                                <div class="company-name-cell">
                                    <div class="company-avatar" style="background-color: ${getRandomColor(company.id)}">
                                        ${getInitials(company.name)}
                                    </div>
                                    <div class="company-info">
                                        <span class="company-name">${company.name}</span>
                                        <span class="company-ca">${company.ca || 'N/A'}</span>
                                    </div>
                                </div>
                            </td>
                            <td><span class="domain-badge">${company.domain || 'Non spécifié'}</span></td>
                            <td>${company.location || 'Non spécifié'}</td>
                            <td>
                                <div class="certifications-list">
                                    ${(company.certifications || []).map(cert => 
                                        `<span class="certification-badge">${cert}</span>`
                                    ).join('')}
                                </div>
                            </td>
                            <td>
                                <div class="score-badge ${getScoreClass(company.score)}">
                                    ${company.score}%
                                </div>
                            </td>
                            <td>
                                <button class="action-button view-details" 
                                        onclick="window.searchApp.viewCompanyDetails('${company.id}')">
                                    Détails
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    function renderStep4Content(panel) {
        panel.innerHTML = `
            <h2>4. Génération de documents</h2>
            
            <div class="document-generation">
                <h3>Documents de consultation</h3>
                <p>Sélectionnez les documents à générer pour votre consultation :</p>
                
                <div class="document-options">
                    <div class="document-card">
                        <input type="checkbox" id="doc-projetMarche" value="projetMarche" checked>
                        <label for="doc-projetMarche">
                            <div class="document-icon">📄</div>
                            <div class="document-info">
                                <h4>Projet de marché</h4>
                                <p>Clauses administratives et techniques</p>
                            </div>
                        </label>
                    </div>
                    
                    <div class="document-card">
                        <input type="checkbox" id="doc-reglementConsultation" value="reglementConsultation" checked>
                        <label for="doc-reglementConsultation">
                            <div class="document-icon">📋</div>
                            <div class="document-info">
                                <h4>Règlement de consultation</h4>
                                <p>Règles de la consultation</p>
                            </div>
                        </label>
                    </div>
                    
                    <div class="document-card">
                        <input type="checkbox" id="doc-lettreConsultation" value="lettreConsultation" checked>
                        <label for="doc-lettreConsultation">
                            <div class="document-icon">✉️</div>
                            <div class="document-info">
                                <h4>Lettre de consultation</h4>
                                <p>Invitation aux entreprises</p>
                            </div>
                        </label>
                    </div>
                    
                    <div class="document-card">
                        <input type="checkbox" id="doc-grilleEvaluation" value="grilleEvaluation" checked>
                        <label for="doc-grilleEvaluation">
                            <div class="document-icon">📊</div>
                            <div class="document-info">
                                <h4>Grille d'évaluation</h4>
                                <p>Grille avec critères d'attribution</p>
                            </div>
                        </label>
                    </div>
                </div>
                
                <div class="project-details">
                    <h3>Informations sur le projet</h3>
                    <div class="form-group">
                        <label for="project-title">Titre du projet</label>
                        <input type="text" id="project-title" 
                               placeholder="Ex: Nettoyage échangeurs à plaques - CNPE Chooz"
                               value="${state.projectData.title}" 
                               onchange="window.searchApp.updateProjectData('title', this.value)">
                    </div>
                    <div class="form-group">
                        <label for="project-description">Description</label>
                        <textarea id="project-description" rows="3" 
                                  placeholder="Description du projet"
                                  onchange="window.searchApp.updateProjectData('description', this.value)">${state.projectData.description}</textarea>
                    </div>
                </div>
                
                <div class="generate-actions">
                    <button class="button primary" onclick="window.searchApp.generateDocuments()">
                        Générer les documents
                    </button>
                </div>
                
                <div class="generated-documents" style="display: none;" id="generated-docs">
                    <h3>Documents générés</h3>
                    <div class="documents-list" id="documents-list">
                        <!-- Rempli dynamiquement -->
                    </div>
                </div>
            </div>
            
            <div class="step-navigation">
                <button class="button secondary" onclick="window.searchApp.goToStep(3)">Retour</button>
            </div>
        `;
    }

    // Fonction de génération de documents
    async function generateDocuments() {
        try {
            // Vérifier si un traitement est en cours
            if (state.isProcessing) {
                showAlert('warning', 'Génération déjà en cours...');
                return;
            }

            state.isProcessing = true;

            // Obtenir les types de documents sélectionnés
            const selectedDocTypes = [];
            document.querySelectorAll('.document-card input[type="checkbox"]:checked').forEach(checkbox => {
                selectedDocTypes.push(checkbox.value);
            });

            if (selectedDocTypes.length === 0) {
                showAlert('warning', 'Veuillez sélectionner au moins un type de document.');
                return;
            }

            // Obtenir les entreprises sélectionnées
            const selectedCompanies = state.selectedCompanies.filter(company => company.selected);
            
            if (selectedCompanies.length === 0) {
                showAlert('warning', 'Veuillez sélectionner au moins une entreprise.');
                return;
            }

            // Afficher l'indicateur de chargement
            showLoading('Génération des documents en cours...');

            // Générer chaque document
            const generatedDocs = [];

            for (const docType of selectedDocTypes) {
                try {
                    const response = await fetch('/api/documents/generate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            templateType: docType,
                            projectData: {
                                ...state.projectData,
                                id: 'P' + Date.now(),
                                selectionCriteria: state.selectionCriteria,
                                attributionCriteria: state.attributionCriteria,
                                cahierDesCharges: state.cahierDesChargesText
                            },
                            companies: selectedCompanies
                        })
                    });

                    if (response.ok) {
                        const data = await response.json();
                        if (data.success) {
                            generatedDocs.push({
                                type: docType,
                                ...data.data
                            });
                        }
                    }
                } catch (error) {
                    console.error(`Erreur génération ${docType}:`, error);
                }
            }

            // Afficher les documents générés
            if (generatedDocs.length > 0) {
                displayGeneratedDocuments(generatedDocs);
                showAlert('success', `${generatedDocs.length} document(s) généré(s) avec succès`);
            } else {
                showAlert('error', 'Aucun document n\'a pu être généré.');
            }

        } catch (error) {
            console.error('Erreur génération documents:', error);
            showAlert('error', `Erreur: ${error.message}`);
        } finally {
            hideLoading();
            state.isProcessing = false;
        }
    }

    function displayGeneratedDocuments(documents) {
        const container = document.getElementById('generated-docs');
        const list = document.getElementById('documents-list');
        
        if (!container || !list) return;
        
        container.style.display = 'block';
        
        const docTypeNames = {
            'projetMarche': { icon: '📄', name: 'Projet de marché' },
            'reglementConsultation': { icon: '📋', name: 'Règlement de consultation' },
            'grilleEvaluation': { icon: '📊', name: 'Grille d\'évaluation' },
            'lettreConsultation': { icon: '✉️', name: 'Lettre de consultation' }
        };
        
        list.innerHTML = documents.map(doc => {
            const docInfo = docTypeNames[doc.type] || { icon: '📄', name: 'Document' };
            
            return `
                <div class="document-item">
                    <div class="document-icon">${docInfo.icon}</div>
                    <div class="document-info">
                        <h4>${docInfo.name}</h4>
                        <p>${doc.fileName}</p>
                    </div>
                    <div class="document-actions">
                        <a href="${doc.fileUrl}" class="button secondary" download>
                            Télécharger
                        </a>
                    </div>
                </div>
            `;
        }).join('');
        
        container.scrollIntoView({ behavior: 'smooth' });
    }

    // Fonction pour voir les détails d'une entreprise
    function viewCompanyDetails(companyId) {
        const company = state.matchedCompanies.find(c => c.id === companyId);
        
        if (!company) {
            showAlert('error', 'Entreprise non trouvée');
            return;
        }
        
        // Créer un modal pour afficher les détails
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Détails de l'entreprise</h3>
                    <button class="close-button" onclick="this.closest('.modal').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="company-details">
                        <div class="company-header">
                            <div class="company-avatar" style="background-color: ${getRandomColor(company.id)}">
                                ${getInitials(company.name)}
                            </div>
                            <div class="company-title">
                                <h2>${company.name}</h2>
                                <p>${company.location}</p>
                            </div>
                        </div>
                        
                        <div class="company-info-grid">
                            <div class="info-item">
                                <div class="info-label">Score de correspondance</div>
                                <div class="info-value">
                                    <div class="score-badge ${getScoreClass(company.score)}">
                                        ${company.score}%
                                    </div>
                                </div>
                            </div>
                            
                            <div class="info-item">
                                <div class="info-label">Domaine</div>
                                <div class="info-value">${company.domain || 'Non spécifié'}</div>
                            </div>
                            
                            <div class="info-item">
                                <div class="info-label">Chiffre d'affaires</div>
                                <div class="info-value">${company.ca || 'Non spécifié'}</div>
                            </div>
                            
                            <div class="info-item">
                                <div class="info-label">Effectifs</div>
                                <div class="info-value">${company.employees || 'Non spécifié'}</div>
                            </div>
                            
                            <div class="info-item">
                                <div class="info-label">Certifications</div>
                                <div class="info-value">
                                    <div class="certifications-list">
                                        ${(company.certifications || []).map(cert => 
                                            `<span class="certification-badge">${cert}</span>`
                                        ).join('') || 'Aucune'}
                                    </div>
                                </div>
                            </div>
                            
                            ${company.experience && company.experience !== 'Non spécifié' ? `
                                <div class="info-item">
                                    <div class="info-label">Expérience</div>
                                    <div class="info-value">${company.experience}</div>
                                </div>
                            ` : ''}
                        </div>
                        
                        ${company.matchDetails ? `
                            <div class="match-details">
                                <h4>Détails des critères</h4>
                                <div class="match-criteria-list">
                                    ${Object.entries(company.matchDetails).map(([criterion, score]) => `
                                        <div class="match-criterion">
                                            <div class="criterion-name">${criterion}</div>
                                            <div class="criterion-score">
                                                <div class="score-progress">
                                                    <div class="progress-bar" style="width: ${score}%"></div>
                                                </div>
                                                <div class="score-value">${score}%</div>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="button secondary" onclick="this.closest('.modal').remove()">Fermer</button>
                    <button class="button primary" onclick="window.searchApp.toggleCompanySelection('${company.id}', ${!company.selected}); this.closest('.modal').remove();">
                        ${company.selected ? 'Déselectionner' : 'Sélectionner'} l'entreprise
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Fermer en cliquant à l'extérieur
        modal.addEventListener('click', e => {
            if (e.target === modal) modal.remove();
        });
    }

    // Fonction pour ajouter une entreprise manuellement
    function addCompanyManually() {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Ajouter une entreprise</h3>
                    <button class="close-button" onclick="this.closest('.modal').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>Nom de l'entreprise</label>
                        <input type="text" id="manual-company-name" required>
                    </div>
                    <div class="form-group">
                        <label>Localisation</label>
                        <input type="text" id="manual-company-location">
                    </div>
                    <div class="form-group">
                        <label>Domaine</label>
                        <select id="manual-company-domain">
                            <option value="Électricité">Électricité</option>
                            <option value="Mécanique">Mécanique</option>
                            <option value="Hydraulique">Hydraulique</option>
                            <option value="Bâtiment">Bâtiment</option>
                            <option value="Maintenance">Maintenance</option>
                            <option value="Autre">Autre</option>
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="button secondary" onclick="this.closest('.modal').remove()">Annuler</button>
                    <button class="button primary" onclick="window.searchApp.saveManualCompany(this.closest('.modal'))">Ajouter</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    function saveManualCompany(modal) {
        const name = modal.querySelector('#manual-company-name').value.trim();
        const location = modal.querySelector('#manual-company-location').value.trim();
        const domain = modal.querySelector('#manual-company-domain').value;
        
        if (!name) {
            showAlert('error', 'Le nom de l\'entreprise est requis.');
            return;
        }
        
        const newCompany = {
            id: 'manual_' + Date.now(),
            name,
            location: location || 'Non spécifié',
            domain,
            certifications: [],
            ca: 'Non spécifié',
            employees: 'Non spécifié',
            score: 100,
            selected: true,
            matchDetails: { 'Ajout manuel': 100 }
        };
        
        state.matchedCompanies.push(newCompany);
        state.selectedCompanies.push(newCompany);
        
        // Mettre à jour l'affichage
        const panel = document.querySelector('.step-panel[data-step="3"]');
        if (panel) {
            renderStep3Content(panel);
        }
        
        modal.remove();
        showAlert('success', 'Entreprise ajoutée avec succès.');
    }

    // Fonctions utilitaires
    function getRandomColor(id) {
        const colors = ['#4285F4', '#34A853', '#FBBC05', '#EA4335', '#673AB7'];
        const index = id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
        return colors[index % colors.length];
    }

    function getInitials(name) {
        return name.split(' ').map(word => word[0]).join('').toUpperCase().substring(0, 2);
    }

    function getScoreClass(score) {
        if (score >= 80) return 'high';
        if (score >= 60) return 'medium';
        return 'low';
    }

    // Fonctions publiques exposées
    window.searchApp = {
        goToStep: goToStep,
        findMatchingCompanies: findMatchingCompanies,
        
        toggleSelectionCriterion: function(id, checked) {
            state.selectionCriteria = state.selectionCriteria.map(criterion => 
                criterion.id == id ? { ...criterion, selected: checked } : criterion
            );
        },
        
        updateAttributionWeight: function(id, weight) {
            state.attributionCriteria = state.attributionCriteria.map(criterion => 
                criterion.id == id ? { ...criterion, weight: parseInt(weight) } : criterion
            );
            updateAttributionTotal();
        },
        
        updateWeightDisplay: function(id, weight) {
            const weightElement = document.querySelector(`.attribution-criterion[data-id="${id}"] .weight-value`);
            if (weightElement) {
                weightElement.textContent = `${weight}%`;
            }
        },
        
        toggleCompanySelection: function(companyId, selected) {
            state.selectedCompanies = state.selectedCompanies.map(company => 
                company.id === companyId ? { ...company, selected } : company
            );
            state.matchedCompanies = state.matchedCompanies.map(company => 
                company.id === companyId ? { ...company, selected } : company
            );
            updateSelectedCount();
        },
        
        updateProjectData: function(field, value) {
            state.projectData[field] = value;
        },
        
        generateDocuments: generateDocuments,
        viewCompanyDetails: viewCompanyDetails,
        addCompanyManually: addCompanyManually,
        saveManualCompany: saveManualCompany
    };

    function updateAttributionTotal() {
        const totalWeight = state.attributionCriteria.reduce((sum, criterion) => sum + criterion.weight, 0);
        const totalElement = document.querySelector('.attribution-total');
        
        if (totalElement) {
            const isValid = totalWeight === 100;
            totalElement.className = `attribution-total ${isValid ? 'valid' : 'invalid'}`;
            totalElement.innerHTML = `
                <span>Total: ${totalWeight}%</span>
                ${isValid ? '<span class="valid-icon">✓</span>' : '<span class="invalid-icon">⚠️</span>'}
            `;
        }
    }

    function updateSelectedCount() {
        const countElement = document.querySelector('.selected-count');
        if (countElement) {
            const selectedCount = state.selectedCompanies.filter(c => c.selected).length;
            countElement.textContent = `${selectedCount} entreprises sélectionnées`;
        }
    }

    console.log("=== SEARCH.JS COMPLET INITIALISÉ ===");
});