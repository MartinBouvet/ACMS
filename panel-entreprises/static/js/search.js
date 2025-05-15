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

 // static/js/search.js (suite)
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
                       <tr class="company-row ${company.selected ? 'selected' : ''}">
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

   // Fonctions utilitaires

   /**
    * Obtient une couleur aléatoire mais cohérente pour un ID
    * @param {String} id - Identifiant
    * @returns {String} - Couleur hexadécimale
    */
   function getRandomColor(id) {
       const colors = [
           '#4285F4', '#34A853', '#FBBC05', '#EA4335',
           '#673AB7', '#3F51B5', '#2196F3', '#03A9F4',
           '#00BCD4', '#009688', '#4CAF50', '#8BC34A',
           '#CDDC39', '#FFC107', '#FF9800', '#FF5722'
       ];
       
       // Utiliser la somme des codes caractères de l'ID pour choisir une couleur
       const sum = id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
       return colors[sum % colors.length];
   }

   /**
    * Obtient les initiales d'un nom
    * @param {String} name - Nom
    * @returns {String} - Initiales
    */
   function getInitials(name) {
       return name
           .split(' ')
           .map(part => part[0])
           .join('')
           .toUpperCase()
           .substring(0, 2);
   }

   /**
    * Détermine la classe CSS pour un score
    * @param {Number} score - Score (0-100)
    * @returns {String} - Classe CSS
    */
   function getScoreClass(score) {
       if (score >= 80) return 'high';
       if (score >= 60) return 'medium';
       return 'low';
   }

   /**
    * Affiche une alerte
    * @param {String} type - Type d'alerte (success, error, warning, info)
    * @param {String} message - Message à afficher
    */
   function showAlert(type, message) {
       // Créer l'élément d'alerte
       const alert = document.createElement('div');
       alert.className = `alert alert-${type}`;
       alert.innerHTML = `
           <div class="alert-icon">${type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️'}</div>
           <div class="alert-message">${message}</div>
           <button class="alert-close">×</button>
       `;
       
       // Ajouter au DOM
       document.body.appendChild(alert);
       
       // Gérer la fermeture
       alert.querySelector('.alert-close').addEventListener('click', () => {
           document.body.removeChild(alert);
       });
       
       // Auto-fermeture après 5 secondes
       setTimeout(() => {
           if (document.body.contains(alert)) {
               document.body.removeChild(alert);
           }
       }, 5000);
   }

   /**
    * Affiche l'indicateur de chargement
    * @param {String} message - Message à afficher
    */
   function showLoading(message) {
       // Créer l'élément de chargement
       const loading = document.createElement('div');
       loading.className = 'loading-overlay';
       loading.innerHTML = `
           <div class="loading-content">
               <div class="spinner"></div>
               <p>${message || 'Chargement en cours...'}</p>
           </div>
       `;
       
       // Ajouter au DOM
       document.body.appendChild(loading);
   }

   /**
    * Cache l'indicateur de chargement
    */
   function hideLoading() {
       const loading = document.querySelector('.loading-overlay');
       if (loading) {
           document.body.removeChild(loading);
       }
   }

   // Exposer certaines fonctions à l'extérieur
   window.searchApp = {
       goToStep,
       toggleSelectionCriterion: (id, checked) => {
           state.selectionCriteria = state.selectionCriteria.map(criterion => 
               criterion.id == id ? { ...criterion, selected: checked } : criterion
           );
       },
    // static/js/search.js (suite finale)
       updateAttributionWeight: (id, value) => {
           state.attributionCriteria = state.attributionCriteria.map(criterion => 
               criterion.id == id ? { ...criterion, weight: parseInt(value) } : criterion
           );
           
           // Mettre à jour l'affichage des poids
           const weightElement = document.querySelector(`.attribution-criterion[data-id="${id}"] .weight-value`);
           if (weightElement) {
               weightElement.textContent = `${value}%`;
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
       },
       toggleCompanySelection: (id, checked) => {
           state.selectedCompanies = state.selectedCompanies.map(company => 
               company.id === id ? { ...company, selected: checked } : company
           );
           
           // Mettre à jour l'affichage
           const row = document.querySelector(`.company-row[data-id="${id}"]`);
           if (row) {
               if (checked) {
                   row.classList.add('selected');
               } else {
                   row.classList.remove('selected');
               }
           }
           
           // Mettre à jour le compteur de sélection
           const countElement = document.querySelector('.selected-count');
           if (countElement) {
               const selectedCount = state.selectedCompanies.filter(c => c.selected).length;
               countElement.textContent = `${selectedCount} entreprises sélectionnées