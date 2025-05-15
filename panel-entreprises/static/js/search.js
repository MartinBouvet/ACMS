// JavaScript for search functionality
// static/js/search.js
document.addEventListener('DOMContentLoaded', function() {
    // État global
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
        }
    };

    // Référence aux éléments DOM
    const stepIndicator = document.querySelector('.step-indicator');
    const stepContent = document.getElementById('step-content');
    const fileDropzone = document.getElementById('file-dropzone');
    const fileInput = document.getElementById('file-input');
    const browseButton = document.getElementById('browse-button');

    // Initialisation des écouteurs d'événements pour l'étape 1
    if (fileDropzone && fileInput && browseButton) {
        initFileUploadListeners();
    }

    /**
     * Initialise les écouteurs d'événements pour le téléversement de fichiers
     */
    function initFileUploadListeners() {
        // Clic sur le dropzone
        fileDropzone.addEventListener('click', function() {
            fileInput.click();
        });

        // Clic sur le bouton "Parcourir"
        browseButton.addEventListener('click', function() {
            fileInput.click();
        });

        // Sélection d'un fichier
        fileInput.addEventListener('change', function(e) {
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

            if (e.dataTransfer.files.length > 0) {
                handleFileSelected(e.dataTransfer.files[0]);
            }
        });
    }

   /**
    * Gère la sélection d'un fichier
    * @param {File} file - Fichier sélectionné
    */
   function handleFileSelected(file) {
       // Vérifier le type de fichier
       const allowedTypes = [
           'application/pdf',
           'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
           'application/msword',
           'text/plain'
       ];
       const maxSize = 10 * 1024 * 1024; // 10 MB

       if (!allowedTypes.includes(file.type)) {
           showAlert('error', 'Type de fichier non supporté. Veuillez utiliser un fichier PDF, DOC, DOCX ou TXT.');
           return;
       }

       if (file.size > maxSize) {
           showAlert('error', 'Fichier trop volumineux. Taille maximum: 10 MB.');
           return;
       }

       // Mettre à jour l'UI pour montrer que le fichier est en cours de traitement
       fileDropzone.innerHTML = `
           <div class="dropzone-content uploading">
               <div class="spinner"></div>
               <p>Analyse en cours...</p>
               <p class="file-name">${file.name}</p>
           </div>
       `;

       // Soumettre le fichier au serveur
       uploadAndParseDocument(file);
   }

   /**
    * Téléverse et analyse le fichier
    * @param {File} file - Fichier à analyser
    */
   async function uploadAndParseDocument(file) {
       try {
           // Créer un FormData
           const formData = new FormData();
           formData.append('file', file);

           // Envoyer le fichier au serveur
           const response = await fetch('/api/files/parse-document', {
               method: 'POST',
               body: formData
           });

           if (!response.ok) {
               throw new Error('Erreur lors du téléversement du fichier');
           }

           const data = await response.json();

           if (!data.success) {
               throw new Error(data.message || 'Erreur lors de l\'analyse du document');
           }

           // Stocker les données
           state.cahierDesCharges = file;
           state.cahierDesChargesText = data.data.text;

           // Analyser le document avec l'IA pour extraire les critères
           analyzeDocumentWithAI(data.data.text);
       } catch (error) {
           console.error('Erreur:', error);
           fileDropzone.innerHTML = `
               <div class="dropzone-content error">
                   <div class="error-icon">❌</div>
                   <p>Erreur: ${error.message}</p>
                   <p>Veuillez réessayer</p>
               </div>
           `;
       }
   }

   /**
    * Analyse le document avec l'API d'IA
    * @param {String} documentText - Texte du document
    */
   async function analyzeDocumentWithAI(documentText) {
       try {
           const response = await fetch('/api/ia/analyze-document', {
               method: 'POST',
               headers: {
                   'Content-Type': 'application/json'
               },
               body: JSON.stringify({ documentText })
           });

           if (!response.ok) {
               throw new Error('Erreur lors de l\'analyse du document');
           }

           const data = await response.json();

           if (!data.success) {
               throw new Error(data.message || 'Erreur lors de l\'analyse du document');
           }

           // Stocker les résultats de l'analyse
           state.keywords = data.data.keywords || [];
           state.selectionCriteria = data.data.selectionCriteria || [];
           state.attributionCriteria = data.data.attributionCriteria || [];

           // Passer à l'étape suivante
           goToStep(2);
       } catch (error) {
           console.error('Erreur:', error);
           fileDropzone.innerHTML = `
               <div class="dropzone-content error">
                   <div class="error-icon">❌</div>
                   <p>Erreur: ${error.message}</p>
                   <p>Veuillez réessayer</p>
               </div>
           `;
       }
   }

   /**
    * Passe à l'étape spécifiée
    * @param {Number} step - Numéro de l'étape
    */
   function goToStep(step) {
       if (step < 1 || step > 4) return;

       // Mettre à jour l'état
       state.currentStep = step;

       // Mettre à jour l'indicateur d'étapes
       updateStepIndicator(step);

       // Mettre à jour le contenu de l'étape
       renderStepContent(step);
   }

   /**
    * Met à jour l'indicateur d'étapes
    * @param {Number} currentStep - Étape actuelle
    */
   function updateStepIndicator(currentStep) {
       const steps = stepIndicator.querySelectorAll('.step');
       const connectors = stepIndicator.querySelectorAll('.step-connector');

       steps.forEach((step, index) => {
           const stepNumber = index + 1;
           
           if (stepNumber < currentStep) {
               // Étape complétée
               step.classList.remove('active');
               step.classList.add('completed');
               step.querySelector('.step-number').innerHTML = '✓';
           } else if (stepNumber === currentStep) {
               // Étape active
               step.classList.add('active');
               step.classList.remove('completed');
               step.querySelector('.step-number').innerHTML = stepNumber;
           } else {
               // Étape future
               step.classList.remove('active', 'completed');
               step.querySelector('.step-number').innerHTML = stepNumber;
           }
       });

       // Mettre à jour les connecteurs
       connectors.forEach((connector, index) => {
           if (index < currentStep - 1) {
               connector.classList.add('completed');
           } else {
               connector.classList.remove('completed');
           }
       });
   }

   /**
    * Rend le contenu de l'étape
    * @param {Number} step - Numéro de l'étape
    */
   function renderStepContent(step) {
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
               // Déjà géré par le HTML
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

       // Marquer le panneau comme actif
       panel.classList.add('active');
   }

   /**
    * Rend le contenu de l'étape 2 (Critères)
    * @param {HTMLElement} panel - Panneau de l'étape
    */
   function renderStep2Content(panel) {
       panel.innerHTML = `
           <h2>2. Mots-clés et critères</h2>
           
           <div class="keywords-section">
               <h3>Mots-clés extraits par l'IA</h3>
               <div class="keywords-container">
                   ${state.keywords.map(keyword => `<span class="keyword-tag">${keyword}</span>`).join('')}
               </div>
           </div>
           
           <div class="criteria-section">
               <h3>Critères de sélection</h3>
               <p>L'IA a identifié les critères suivants basés sur votre cahier des charges :</p>
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

       // Initialiser les écouteurs d'événements pour les critères
       initCriteriaListeners();
   }

   /**
    * Rend le contenu HTML pour les critères de sélection
    * @returns {String} HTML des critères de sélection
    */
   function renderSelectionCriteria() {
       if (!state.selectionCriteria || state.selectionCriteria.length === 0) {
           return '<p class="empty-state">Aucun critère trouvé</p>';
       }

       return state.selectionCriteria.map((criterion, index) => `
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

   /**
    * Rend le contenu HTML pour les critères d'attribution
    * @returns {String} HTML des critères d'attribution
    */
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
               ${state.attributionCriteria.map((criterion) => `
                   <div class="attribution-criterion" data-id="${criterion.id}">
                       <div class="criterion-name">${criterion.name}</div>
                       <div class="criterion-weight">
                           <input type="range" min="0" max="100" step="5" value="${criterion.weight}"
                                  onchange="window.searchApp.updateAttributionWeight(${criterion.id}, this.value)">
                           <span class="weight-value">${criterion.weight}%</span>
                       </div>
                   </div>
               `).join('')}
           </div>
       `;
   }

   /**
    * Initialise les écouteurs d'événements pour les critères
    */
   function initCriteriaListeners() {
       // Les écouteurs sont définis directement dans les éléments HTML via les attributs onchange
   }

   /**
    * Recherche les entreprises correspondant aux critères
    */
   async function findMatchingCompanies() {
       try {
           // Afficher l'indicateur de chargement
           showLoading('Recherche des entreprises correspondantes...');

           // Appeler l'API pour trouver les entreprises
           const response = await fetch('/api/ia/find-matching-companies', {
               method: 'POST',
               headers: {
                   'Content-Type': 'application/json'
               },
               body: JSON.stringify({
                   criteria: state.selectionCriteria
               })
           });

           if (!response.ok) {
               throw new Error('Erreur lors de la recherche d\'entreprises');
           }

           const data = await response.json();

           if (!data.success) {
               throw new Error(data.message || 'Erreur lors de la recherche d\'entreprises');
           }

           // Stocker les entreprises trouvées
           state.matchedCompanies = data.data || [];
           state.selectedCompanies = state.matchedCompanies.map(company => ({
               ...company,
               selected: true
           }));

           // Passer à l'étape suivante
           goToStep(3);
       } catch (error) {
           console.error('Erreur:', error);
           showAlert('error', error.message);
           hideLoading();
       }
   }

   /**
    * Rend le contenu de l'étape 3 (Liste des entreprises)
    * @param {HTMLElement} panel - Panneau de l'étape
    */
   function renderStep3Content(panel) {
       panel.innerHTML = `
           <h2>3. Panel d'entreprises</h2>
           
           <div class="companies-result">
               <h3>Entreprises correspondant à vos critères</h3>
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

   /**
    * Rend le tableau des entreprises
    * @returns {String} HTML du tableau des entreprises
    */
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
                       <th>Localisation</th>
                       <th>Certifications</th>
                       <th>Score</th>
                       <th>Actions</th>
                   </tr>
               </thead>
               <tbody>
                   ${state.matchedCompanies.map((company, index) => `
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
                                   <div class="company-avatar" style="background-color: ${utils.getRandomColor(company.id)}">
                                       ${utils.getInitials(company.name)}
                                   </div>
                                   <div class="company-info">
                                       <span class="company-name">${company.name}</span>
                                       <span class="company-ca">${company.ca}</span>
                                   </div>
                               </div>
                           </td>
                           <td>${company.location}</td>
                           <td>
                               <div class="certifications-list">
                                   ${(company.certifications || []).map(cert => 
                                       `<span class="certification-badge">${cert}</span>`
                                   ).join('')}
                               </div>
                           </td>
                           <td>
                               <div class="score-badge ${utils.getScoreClass(company.score)}">
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

   /**
    * Rend le contenu de l'étape 4 (Génération de documents)
    * @param {HTMLElement} panel - Panneau de l'étape
    */
   function renderStep4Content(panel) {
       panel.innerHTML = `
           <h2>4. Génération de documents</h2>
           
           <div class="document-generation">
               <h3>Sélectionnez les documents à générer</h3>
               
               <div class="document-options">
                   <div class="document-card">
                       <input type="checkbox" id="doc-projetMarche" value="projetMarche" checked>
                       <label for="doc-projetMarche">
                           <div class="document-icon">📄</div>
                           <div class="document-info">
                               <h4>Projet de marché</h4>
                               <p>Document type incluant les clauses administratives et techniques</p>
                           </div>
                       </label>
                   </div>
                   
                   <div class="document-card">
                       <input type="checkbox" id="doc-reglementConsultation" value="reglementConsultation" checked>
                       <label for="doc-reglementConsultation">
                           <div class="document-icon">📋</div>
                           <div class="document-info">
                               <h4>Règlement de consultation</h4>
                               <p>Document définissant les règles de la consultation</p>
                           </div>
                       </label>
                   </div>
                   
                   <div class="document-card">
                       <input type="checkbox" id="doc-grilleEvaluation" value="grilleEvaluation" checked>
                       <label for="doc-grilleEvaluation">
                           <div class="document-icon">📊</div>
                           <div class="document-info">
                               <h4>Grille d'évaluation</h4>
                               <p>Grille pré-remplie avec vos critères d'attribution</p>
                           </div>
                       </label>
                   </div>
                   
                   <div class="document-card">
                       <input type="checkbox" id="doc-lettreConsultation" value="lettreConsultation" checked>
                       <label for="doc-lettreConsultation">
                           <div class="document-icon">✉️</div>
                           <div class="document-info">
                               <h4>Lettre de consultation</h4>
                               <p>Lettre type pour inviter les entreprises à consulter</p>
                           </div>
                       </label>
                   </div>
               </div>
               
               <div class="project-details">
                   <h3>Informations sur le projet</h3>
                   <div class="form-group">
                       <label for="project-title">Titre du projet</label>
                       <input type="text" id="project-title" placeholder="Ex: Rénovation système électrique site XYZ"
                              value="${state.projectData.title}" 
                              onchange="window.searchApp.updateProjectData('title', this.value)">
                   </div>
                   <div class="form-group">
                       <label for="project-description">Description</label>
                       <textarea id="project-description" rows="3" 
                                 placeholder="Brève description du projet"
                                 onchange="window.searchApp.updateProjectData('description', this.value)">${state.projectData.description}</textarea>
                   </div>
               </div>
               
               <div class="generate-actions">
                   <button class="button primary" id="generate-button" onclick="window.searchApp.generateDocuments()">
                       Générer les documents
                   </button>
               </div>
               
               <div class="generated-documents" style="display: none;">
                   <h3>Documents générés</h3>
                   <div class="documents-list" id="documents-list">
                       <!-- Liste des documents générés -->
                   </div>
               </div>
           </div>
           
           <div class="step-navigation">
               <button class="button secondary" onclick="window.searchApp.goToStep(3)">Retour</button>
           </div>
       `;
   }

   /**
    * Génère les documents de consultation
    */
   async function generateDocuments() {
       try {
           // Obtenir les types de documents sélectionnés
           const selectedDocTypes = [];
           document.querySelectorAll('.document-card input[type="checkbox"]:checked').forEach(checkbox => {
               selectedDocTypes.push(checkbox.value);
           });

           if (selectedDocTypes.length === 0) {
               showAlert('warning', 'Veuillez sélectionner au moins un type de document à générer.');
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

           // Pour chaque type de document, appeler l'API
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

                   if (!response.ok) {
                       console.error(`Erreur lors de la génération du document ${docType}`);
                       continue;
                   }

                   const data = await response.json();

                   if (data.success) {
                       generatedDocs.push({
                           type: docType,
                           ...data.data
                       });
                   }
               } catch (error) {
                   console.error(`Erreur lors de la génération du document ${docType}:`, error);
               }
           }

           // Cacher l'indicateur de chargement
           hideLoading();

           // Afficher les documents générés
           if (generatedDocs.length > 0) {
               displayGeneratedDocuments(generatedDocs);
           } else {
               showAlert('error', 'Aucun document n\'a pu être généré. Veuillez réessayer.');
           }
       } catch (error) {
           console.error('Erreur:', error);
           hideLoading();
           showAlert('error', 'Erreur lors de la génération des documents: ' + error.message);
       }
   }

   /**
    * Affiche les documents générés
    * @param {Array} documents - Liste des documents générés
    */
   function displayGeneratedDocuments(documents) {
       const container = document.querySelector('.generated-documents');
       const list = document.getElementById('documents-list');
       
       if (!container || !list) return;
       
       // Afficher le conteneur
       container.style.display = 'block';
       
       // Remplir la liste des documents
       list.innerHTML = documents.map(doc => {
           let icon, title;
           
           switch (doc.type) {
               case 'projetMarche':
                   icon = '📄';
                   title = 'Projet de marché';
                   break;
               case 'reglementConsultation':
                   icon = '📋';
                   title = 'Règlement de consultation';
                   break;
               case 'grilleEvaluation':
                   icon = '📊';
                   title = 'Grille d\'évaluation';
                   break;
               case 'lettreConsultation':
                   icon = '✉️';
                   title = 'Lettre de consultation';
                   break;
               default:
                   icon = '📄';
                   title = 'Document';
           }
           
           return `
               <div class="document-item">
                   <div class="document-icon">${icon}</div>
                   <div class="document-info">
                       <h4>${title}</h4>
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
       
       // Faire défiler jusqu'aux documents
       container.scrollIntoView({ behavior: 'smooth' });
   }

   /**
    * Affiche les détails d'une entreprise
    * @param {String} companyId - ID de l'entreprise
    */
   function viewCompanyDetails(companyId) {
       const company = state.matchedCompanies.find(c => c.id === companyId);
       
       if (!company) return;
       
       // Créer un modal pour afficher les détails
       const modal = document.createElement('div');
       modal.className = 'modal';
       modal.innerHTML = `
           <div class="modal-content">
               <div class="modal-header">
                   <h3>Détails de l'entreprise</h3>
                   <button class="close-button">&times;</button>
               </div>
               <div class="modal-body">
                   <div class="company-details">
                       <div class="company-header">
                           <div class="company-avatar" style="background-color: ${utils.getRandomColor(company.id)}">
                               ${utils.getInitials(company.name)}
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
                                   <div class="score-badge ${utils.getScoreClass(company.score)}">
                                       ${company.score}%
                                   </div>
                               </div>
                           </div>
                           
                           <div class="info-item">
                               <div class="info-label">Chiffre d'affaires</div>
                               <div class="info-value">${company.ca}</div>
                           </div>
                           
                           <div class="info-item">
                               <div class="info-label">Effectifs</div>
                               <div class="info-value">${company.employees}</div>
                           </div>
                           
                           <div class="info-item">
                               <div class="info-label">Certifications</div>
                               <div class="info-value">
                                   <div class="certifications-list">
                                       ${(company.certifications || []).map(cert => 
                                           `<span class="certification-badge">${cert}</span>`
                                       ).join('')}
                                   </div>
                               </div>
                           </div>
                           
                           <div class="info-item">
                               <div class="info-label">Expérience</div>
                               <div class="info-value">${company.experience || 'Non spécifié'}</div>
                           </div>
                       </div>
                       
                       <div class="match-details">
                           <h4>Détails des critères</h4>
                           <div class="match-criteria-list">
                               ${Object.entries(company.matchDetails || {}).map(([criterion, score]) => `
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
                   </div>
               </div>
               <div class="modal-footer">
                   <button class="button secondary" data-close-modal>Fermer</button>
                   <button class="button primary" onclick="window.searchApp.toggleCompanySelection('${company.id}', ${!company.selected})">
                       ${company.selected ? 'Déselectionner' : 'Sélectionner'} l'entreprise
                   </button>
               </div>
           </div>
       `;
       
       // Ajouter le modal au DOM
       document.body.appendChild(modal);
       
       // Gérer la fermeture du modal
       const closeButton = modal.querySelector('.close-button');
       const closeModalButton = modal.querySelector('[data-close-modal]');
       
       const closeModal = () => {
           document.body.removeChild(modal);
       };
       
       closeButton.addEventListener('click', closeModal);
       closeModalButton.addEventListener('click', closeModal);
       
       // Fermer le modal en cliquant à l'extérieur
       modal.addEventListener('click', e => {
           if (e.target === modal) closeModal();
       });
   }

   /**
    * Ajoute une entreprise manuellement
    */
   function addCompanyManually() {
       // Créer un modal pour ajouter une entreprise
       const modal = document.createElement('div');
       modal.className = 'modal';
       modal.innerHTML = `
           <div class="modal-content">
               <div class="modal-header">
                   <h3>Ajouter une entreprise</h3>
                   <button class="close-button">&times;</button>
               </div>
               <div class="modal-body">
                   <div class="form-group">
                       <label for="company-name">Nom de l'entreprise</label>
                       <input type="text" id="company-name" placeholder="Nom de l'entreprise" required>
                   </div>
                   <div class="form-group">
                       <label for="company-location">Localisation</label>
                       <input type="text" id="company-location" placeholder="Ville, Département">
                   </div>
                   <div class="form-group">
                       <label for="company-ca">Chiffre d'affaires</label>
                       <input type="text" id="company-ca" placeholder="Ex: 1.5M€">
                   </div>
                   <div class="form-group">
                       <label for="company-employees">Effectifs</label>
                       <input type="text" id="company-employees" placeholder="Ex: 25">
                   </div>
                   <div class="form-group">
                       <label>Certifications</label>
                       <div class="certifications-checkboxes">
                           <label class="checkbox-label">
                               <input type="checkbox" value="MASE"> MASE
                           </label>
                           <label class="checkbox-label">
                               <input type="checkbox" value="ISO 9001"> ISO 9001
                           </label>
                           <label class="checkbox-label">
                               <input type="checkbox" value="ISO 14001"> ISO 14001
                           </label>
                           <label class="checkbox-label">
                               <input type="checkbox" value="QUALIBAT"> QUALIBAT
                           </label>
                       </div>
                   </div>
               </div>
               <div class="modal-footer">
                   <button class="button secondary" data-close-modal>Annuler</button>
                   <button class="button primary" id="save-company">Ajouter</button>
               </div>
           </div>
       `;
       
       // Ajouter le modal au DOM
       document.body.appendChild(modal);
       
       // Gérer la fermeture du modal
       const closeButton = modal.querySelector('.close-button');
       const closeModalButton = modal.querySelector('[data-close-modal]');
       const saveButton = modal.querySelector('#save-company');
       
       const closeModal = () => {
           document.body.removeChild(modal);
       };
       
       closeButton.addEventListener('click', closeModal);
       closeModalButton.addEventListener('click', closeModal);
       
       // Enregistrer l'entreprise
       saveButton.addEventListener('click', () => {
           const name = modal.querySelector('#company-name').value.trim();
           const location = modal.querySelector('#company-location').value.trim();
           const ca = modal.querySelector('#company-ca').value.trim();
           const employees = modal.querySelector('#company-employees').value.trim();
           
           if (!name) {
               showAlert('error', 'Le nom de l\'entreprise est requis.');
               return;
           }
           
           // Récupérer les certifications cochées
           const certifications = [];
           modal.querySelectorAll('.certifications-checkboxes input:checked').forEach(checkbox => {
               certifications.push(checkbox.value);
           });
           
           // Créer l'objet entreprise
           const newCompany = {
               id: 'manual_' + Date.now(),
               name,
               location: location || 'Non spécifié',
               ca: ca || 'Non spécifié',
               employees: employees || 'Non spécifié',
               certifications,
               score: 100,  // Score par défaut pour les entreprises ajoutées manuellement
               selected: true,
               matchDetails: {
                   'Ajout manuel': 100
               }
           };
           
           // Ajouter l'entreprise à l'état
           state.matchedCompanies.push(newCompany);
           state.selectedCompanies.push(newCompany);
           
           // Mettre à jour l'affichage
           const panel = document.querySelector('.step-panel[data-step="3"]');
           if (panel) {
               renderStep3Content(panel);
           }
           
           // Fermer le modal
           closeModal();
           
           // Afficher une confirmation
           showAlert('success', 'Entreprise ajoutée avec succès.');
       });
       
       // Fermer le modal en cliquant à l'extérieur
       modal.addEventListener('click', e => {
           if (e.target === modal) closeModal();
       });
   }

   /**
    * Active/désactive la sélection d'une entreprise
    * @param {String} companyId - ID de l'entreprise
    * @param {Boolean} selected - État de sélection
    */
   function toggleCompanySelection(companyId, selected) {
       // Mettre à jour l'état des entreprises
       state.selectedCompanies = state.selectedCompanies.map(company => 
           company.id === companyId ? { ...company, selected } : company
       );
       
       // Mettre à jour l'affichage du tableau
       const row = document.querySelector(`.company-row[data-id="${companyId}"]`);
       if (row) {
           if (selected) {
               row.classList.add('selected');
           } else {
               row.classList.remove('selected');
           }
           
           const checkbox = row.querySelector('input[type="checkbox"]');
           if (checkbox) {
               checkbox.checked = selected;
           }
       }
       
       // Mettre à jour le compteur de sélection
       const countElement = document.querySelector('.selected-count');
       if (countElement) {
           const selectedCount = state.selectedCompanies.filter(c => c.selected).length;
           countElement.textContent = `${selectedCount} entreprises sélectionnées`;
       }
   }

   /**
    * Met à jour les données du projet
    * @param {String} field - Champ à modifier
    * @param {String} value - Nouvelle valeur
    */
   function updateProjectData(field, value) {
       state.projectData[field] = value;
   }

   /**
    * Met à jour le poids d'un critère d'attribution
    * @param {Number} id - ID du critère
    * @param {Number} weight - Nouveau poids
    */
   function updateAttributionWeight(id, weight) {
       state.attributionCriteria = state.attributionCriteria.map(criterion => 
           criterion.id == id ? { ...criterion, weight: parseInt(weight) } : criterion
       );
       
       // Mettre à jour l'affichage des poids
       const weightElement = document.querySelector(`.attribution-criterion[data-id="${id}"] .weight-value`);
       if (weightElement) {
           weightElement.textContent = `${weight}%`;
       }
       
       // Mettre à jour le total
       const totalWeight = state.attributionCriteria.reduce((sum, criterion) => sum + criterion.weight, 0);
       const totalElement = document.querySelector('.attribution-total');
       
       if (totalElement) {
           totalElement.innerHTML = `
               <span>Total: ${totalWeight}%</span>
               ${totalWeight === 100 
                   ? '<span class="valid-icon">✓</span>' 
                   : '<span class="invalid-icon">⚠️</span>'}
           `;
           totalElement.className = `attribution-total ${totalWeight === 100 ? 'valid' : 'invalid'}`;
       }
   }

   /**
    * Active/désactive un critère de sélection
    * @param {Number} id - ID du critère
    * @param {Boolean} checked - État d'activation
    */
   function toggleSelectionCriterion(id, checked) {
       state.selectionCriteria = state.selectionCriteria.map(criterion => 
           criterion.id == id ? { ...criterion, selected: checked } : criterion
       );
   }

   // Exposer certaines fonctions à l'extérieur
   window.searchApp = {
       goToStep,
       findMatchingCompanies,
       toggleCompanySelection,
       viewCompanyDetails,
       addCompanyManually,
       generateDocuments,
       updateProjectData,
       updateAttributionWeight,
       toggleSelectionCriterion
   };
});