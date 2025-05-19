/**
 * dashboard.js - Gestion du tableau de bord
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialiser les composants du tableau de bord
    initDashboard();
    
    // Initialiser les onglets
    initTabs();
});

/**
 * Initialise les composants du tableau de bord
 */
function initDashboard() {
    initCharts();
    initActivityUpdates();
    initPeriodSelector();
    initProjectFilters();
}

/**
 * Initialise les graphiques du tableau de bord
 */
function initCharts() {
    // Simuler un graphique d'évolution des projets
    renderProjectEvolutionChart();
    
    // Initialiser les graphiques des onglets Analytics
    if (document.getElementById('tab-analytics')) {
        initAnalyticsCharts();
    }
}

/**
 * Initialise les mises à jour d'activité
 */
function initActivityUpdates() {
    // Pour une démonstration, on peut ajouter un intervalle pour simuler de nouvelles activités
    // qui s'ajouteraient en temps réel
    
    /* 
    // Désactivé pour l'instant
    setInterval(() => {
        const activityList = document.querySelector('.activity-list');
        if (activityList && Math.random() > 0.7) { // 30% de chance d'ajouter une activité
            addNewActivity(activityList);
        }
    }, 30000); // Toutes les 30 secondes
    */
}

/**
 * Ajoute une nouvelle activité à la liste
 * @param {HTMLElement} container - Conteneur de la liste d'activités
 */
function addNewActivity(container) {
    const activities = [
        {
            icon: '📝',
            title: 'Nouveau projet créé',
            timestamp: 'À l\'instant'
        },
        {
            icon: '👥',
            title: 'Panel d\'entreprises mis à jour',
            timestamp: 'À l\'instant'
        },
        {
            icon: '📄',
            title: 'Documents générés pour un projet',
            timestamp: 'À l\'instant'
        }
    ];
    
    const randomActivity = activities[Math.floor(Math.random() * activities.length)];
    
    const activityItem = document.createElement('div');
    activityItem.className = 'activity-item';
    activityItem.style.opacity = '0';
    activityItem.style.transform = 'translateY(-10px)';
    activityItem.style.transition = 'all 0.3s ease';
    
    activityItem.innerHTML = `
        <div class="activity-icon">${randomActivity.icon}</div>
        <div class="activity-content">
            <div class="activity-title">${randomActivity.title}</div>
            <div class="activity-timestamp">${randomActivity.timestamp}</div>
        </div>
    `;
    
    // Insérer au début de la liste
    container.insertBefore(activityItem, container.firstChild);
    
    // Animation d'apparition
    setTimeout(() => {
        activityItem.style.opacity = '1';
        activityItem.style.transform = 'translateY(0)';
    }, 100);
    
    // Limiter le nombre d'activités affichées
    const activityItems = container.querySelectorAll('.activity-item');
    if (activityItems.length > 5) {
        container.removeChild(activityItems[activityItems.length - 1]);
    }
}

/**
 * Initialise le sélecteur de période
 */
function initPeriodSelector() {
    const periodOptions = document.querySelectorAll('.period-option');
    
    periodOptions.forEach(option => {
        option.addEventListener('click', function() {
            // Retirer la classe active de tous les boutons
            periodOptions.forEach(btn => btn.classList.remove('active'));
            
            // Ajouter la classe active au bouton cliqué
            this.classList.add('active');
            
            // Mettre à jour le graphique en fonction de la période
            const period = this.textContent.toLowerCase();
            updateChartForPeriod(period);
        });
    });
}

/**
 * Met à jour le graphique en fonction de la période sélectionnée
 * @param {string} period - Période sélectionnée (semaine, mois, trimestre, année)
 */
function updateChartForPeriod(period) {
    // Simuler un changement de graphique
    renderProjectEvolutionChart(period);
}

/**
 * Rend le graphique d'évolution des projets
 * @param {string} period - Période à afficher (défaut: 'mois')
 */
function renderProjectEvolutionChart(period = 'mois') {
    const chartContainer = document.querySelector('.chart-container');
    
    if (!chartContainer) return;
    
    // Pour l'instant, on affiche juste un placeholder
    // Dans une implémentation réelle, on utiliserait une bibliothèque comme Chart.js
    
    chartContainer.innerHTML = `
        <div class="chart-placeholder">
            <div class="placeholder-icon">📊</div>
            <p>Graphique d'évolution des projets (${period})</p>
            <p class="chart-note">Cette fonctionnalité sera implémentée avec Chart.js</p>
        </div>
    `;
}

/**
 * Initialise les filtres de projets
 */
function initProjectFilters() {
    const statusFilter = document.getElementById('project-status-filter');
    const dateFilter = document.getElementById('project-date-filter');
    const searchInput = document.getElementById('project-search');
    
    if (statusFilter) {
        statusFilter.addEventListener('change', filterProjects);
    }
    
    if (dateFilter) {
        dateFilter.addEventListener('change', filterProjects);
    }
    
    if (searchInput) {
        searchInput.addEventListener('input', filterProjects);
    }
}

/**
 * Filtre les projets selon les critères sélectionnés
 */
function filterProjects() {
    const statusFilter = document.getElementById('project-status-filter');
    const dateFilter = document.getElementById('project-date-filter');
    const searchInput = document.getElementById('project-search');
    
    if (!statusFilter || !dateFilter || !searchInput) return;
    
    const statusValue = statusFilter.value;
    const dateValue = dateFilter.value;
    const searchValue = searchInput.value.toLowerCase();
    
    const projectRows = document.querySelectorAll('.projects-table tbody tr');
    
    projectRows.forEach(row => {
        const projectName = row.cells[0].textContent.toLowerCase();
        const projectStatus = row.cells[1].textContent.toLowerCase();
        
        // Filtrer par statut
        const matchesStatus = statusValue === 'all' || 
                             (statusValue === 'active' && projectStatus.includes('en cours')) ||
                             (statusValue === 'pending' && projectStatus.includes('à venir')) ||
                             (statusValue === 'completed' && projectStatus.includes('terminé'));
        
        // Filtrer par recherche
        const matchesSearch = searchValue === '' || projectName.includes(searchValue);
        
        // Date filter is a bit more complex in real implementation
        // Here's a simplified version that always matches
        const matchesDate = true;
        
        // Afficher ou masquer la ligne
        if (matchesStatus && matchesSearch && matchesDate) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

/**
 * Initialise les graphiques pour l'onglet Analyses
 */
function initAnalyticsCharts() {
    const chartContainers = document.querySelectorAll('#tab-analytics .chart-container');
    
    chartContainers.forEach(container => {
        // Pour l'instant, on garde les placeholders
        // Dans une implémentation réelle, on utiliserait Chart.js
    });
}

/**
 * Initialise les onglets du tableau de bord
 */
function initTabs() {
    const tabs = document.querySelectorAll('.dashboard-tab');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            switchTab(tabId);
        });
    });
}

/**
 * Change l'onglet actif
 * @param {string} tabId - ID de l'onglet à activer
 */
function switchTab(tabId) {
    // Désactiver tous les onglets
    document.querySelectorAll('.dashboard-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Désactiver tous les contenus d'onglets
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Activer l'onglet sélectionné
    const selectedTab = document.querySelector(`.dashboard-tab[data-tab="${tabId}"]`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Activer le contenu de l'onglet sélectionné
    const selectedContent = document.getElementById(`tab-${tabId}`);
    if (selectedContent) {
        selectedContent.classList.add('active');
    }
}

// Exporter les fonctions pour une utilisation externe
window.dashboardUtils = {
    updateChartForPeriod,
    switchTab,
    filterProjects
};