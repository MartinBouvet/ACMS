/**
 * criteria.js - Gestion des critères de sélection et d'attribution
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialiser les gestionnaires d'événements pour les critères
    initCriteriaEvents();
});

/**
 * Initialise les gestionnaires d'événements pour les critères
 */
function initCriteriaEvents() {
    initSelectionCriteriaEvents();
    initAttributionCriteriaEvents();
}

/**
 * Initialise les gestionnaires pour les critères de sélection
 */
function initSelectionCriteriaEvents() {
    // Gestionnaires pour les toggles de critères de sélection
    const selectionToggles = document.querySelectorAll('.criterion-card .toggle-switch input[type="checkbox"]');
    
    selectionToggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const criterionId = this.closest('.criterion-card').dataset.id;
            toggleSelectionCriterion(criterionId, this.checked);
        });
    });
}

/**
 * Active/désactive un critère de sélection
 * 
 * @param {string|number} criterionId - ID du critère
 * @param {boolean} checked - État d'activation
 */
function toggleSelectionCriterion(criterionId, checked) {
    // Cette fonction sera exposée à searchApp, voir search.js
    if (window.searchApp && window.searchApp.toggleSelectionCriterion) {
        window.searchApp.toggleSelectionCriterion(criterionId, checked);
    } else {
        console.log(`Critère ${criterionId} ${checked ? 'activé' : 'désactivé'}`);
    }
}

/**
 * Initialise les gestionnaires pour les critères d'attribution
 */
function initAttributionCriteriaEvents() {
    // Gestionnaires pour les sliders de poids d'attribution
    const attributionSliders = document.querySelectorAll('.attribution-criterion input[type="range"]');
    
    attributionSliders.forEach(slider => {
        // Mise à jour en temps réel pendant le glissement
        slider.addEventListener('input', function() {
            const weightValue = this.closest('.criterion-weight').querySelector('.weight-value');
            if (weightValue) {
                weightValue.textContent = `${this.value}%`;
            }
        });
        
        // Mise à jour finale après le relâchement
        slider.addEventListener('change', function() {
            const criterionId = this.closest('.attribution-criterion').dataset.id;
            updateAttributionWeight(criterionId, this.value);
        });
    });
}

/**
 * Met à jour le poids d'un critère d'attribution
 * 
 * @param {string|number} criterionId - ID du critère
 * @param {number} weight - Nouveau poids
 */
function updateAttributionWeight(criterionId, weight) {
    // Cette fonction sera exposée à searchApp, voir search.js
    if (window.searchApp && window.searchApp.updateAttributionWeight) {
        window.searchApp.updateAttributionWeight(criterionId, weight);
    } else {
        // Mise à jour visuelle temporaire
        const criterionElem = document.querySelector(`.attribution-criterion[data-id="${criterionId}"]`);
        if (criterionElem) {
            const weightValue = criterionElem.querySelector('.weight-value');
            if (weightValue) {
                weightValue.textContent = `${weight}%`;
            }
        }
        
        // Recalculer le total
        updateAttributionTotal();
    }
}

/**
 * Met à jour l'affichage du total des poids des critères d'attribution
 */
function updateAttributionTotal() {
    const weightElements = document.querySelectorAll('.attribution-criterion .weight-value');
    let total = 0;
    
    weightElements.forEach(element => {
        const weight = parseInt(element.textContent);
        if (!isNaN(weight)) {
            total += weight;
        }
    });
    
    const totalElement = document.querySelector('.attribution-total');
    if (totalElement) {
        totalElement.innerHTML = `
            <span>Total: ${total}%</span>
            ${total === 100 
                ? '<span class="valid-icon">✓</span>' 
                : '<span class="invalid-icon">⚠️</span>'}
        `;
        totalElement.className = `attribution-total ${total === 100 ? 'valid' : 'invalid'}`;
    }
}

/**
 * Génère le HTML pour afficher les critères de sélection
 * 
 * @param {Array} criteria - Liste des critères de sélection
 * @returns {string} - HTML pour afficher les critères
 */
function renderSelectionCriteria(criteria) {
    if (!criteria || criteria.length === 0) {
        return '<p class="empty-state">Aucun critère trouvé</p>';
    }
    
    return criteria.map(criterion => `
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
 * Génère le HTML pour afficher les critères d'attribution
 * 
 * @param {Array} criteria - Liste des critères d'attribution
 * @returns {string} - HTML pour afficher les critères
 */
function renderAttributionCriteria(criteria) {
    if (!criteria || criteria.length === 0) {
        return '<p class="empty-state">Aucun critère trouvé</p>';
    }
    
    const totalWeight = criteria.reduce((sum, criterion) => sum + criterion.weight, 0);
    const isValid = totalWeight === 100;
    
    return `
        <div class="attribution-total ${isValid ? 'valid' : 'invalid'}">
            <span>Total: ${totalWeight}%</span>
            ${isValid ? '<span class="valid-icon">✓</span>' : '<span class="invalid-icon">⚠️</span>'}
        </div>
        
        <div class="attribution-criteria-list">
            ${criteria.map((criterion) => `
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

// Exporter les fonctions pour une utilisation externe
window.criteriaUtils = {
    toggleSelectionCriterion,
    updateAttributionWeight,
    updateAttributionTotal,
    renderSelectionCriteria,
    renderAttributionCriteria
};