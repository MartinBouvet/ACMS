/**
 * dashboard.js - Gestion du tableau de bord
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialiser les composants du tableau de bord
    initDashboard();
});

/**
 * Initialise les composants du tableau de bord
 */
function initDashboard() {
    initCharts();
    initActivityUpdates();
    initPeriodSelector();
}

/**
 * Initialise les graphiques du tableau de bord
 */
function initCharts() {
    // Simuler un graphique d'évolution des projets
    renderProjectEvolutionChart();
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
 * 
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
 * 
 * @param {string} period - Période sélectionnée (semaine, mois, trimestre, année)
 */
function updateChartForPeriod(period) {
    // Simuler un changement de graphique
    renderProjectEvolutionChart(period);
}

/**
 * Rend le graphique d'évolution des projets
 * 
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
    
    // Exemple d'implémentation avec Chart.js (commenté pour le moment)
    /*
    // Données simulées
    const labels = {
        'semaine': ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
        'mois': ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'],
        'trimestre': ['T1', 'T2', 'T3', 'T4'],
        'année': ['2021', '2022', '2023', '2024', '2025']
    };
    
    const data = {
        'semaine': [2, 5, 3, 7, 4, 1, 3],
        'mois': [4, 6, 8, 9, 7, 6, 10, 8, 7, 9, 8, 10],
        'trimestre': [15, 22, 19, 25],
        'année': [45, 60, 75, 82, 95]
    };
    
    // Créer le canvas pour le graphique
    chartContainer.innerHTML = '<canvas id="projectEvolutionChart"></canvas>';
    const ctx = document.getElementById('projectEvolutionChart').getContext('2d');
    
    // Créer le graphique
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels[period],
            datasets: [{
                label: 'Nombre de projets',
                data: data[period],
                backgroundColor: 'rgba(0, 114, 188, 0.2)',
                borderColor: 'rgba(0, 114, 188, 1)',
                borderWidth: 2,
                tension: 0.3,
                pointBackgroundColor: 'rgba(0, 114, 188, 1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
    */
}

// Exporter les fonctions pour une utilisation externe
window.dashboardUtils = {
    updateChartForPeriod
};