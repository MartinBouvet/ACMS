// Utility JavaScript functions
/**
 * utils.js - Fonctions utilitaires pour l'application Panel Entreprises
 */

/**
 * Génère une couleur cohérente basée sur un identifiant
 * @param {String} id - Identifiant
 * @returns {String} Couleur hexadécimale
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
 * Extrait les initiales d'un nom
 * @param {String} name - Nom
 * @returns {String} Initiales (max 2 caractères)
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
 * @returns {String} Classe CSS (high, medium, low)
 */
function getScoreClass(score) {
    if (score >= 80) return 'high';
    if (score >= 60) return 'medium';
    return 'low';
}

/**
 * Formate un nombre avec séparateur de milliers
 * @param {Number} num - Nombre à formater
 * @returns {String} Nombre formaté
 */
function formatNumber(num) {
    return new Intl.NumberFormat('fr-FR').format(num);
}

/**
 * Tronque un texte s'il dépasse une certaine longueur
 * @param {String} text - Texte à tronquer
 * @param {Number} length - Longueur maximale
 * @returns {String} Texte tronqué
 */
function truncateText(text, length = 100) {
    if (!text || text.length <= length) return text;
    return text.substring(0, length) + '...';
}

/**
 * Convertit une chaîne en slug (URL friendly)
 * @param {String} text - Texte à convertir
 * @returns {String} Slug
 */
function slugify(text) {
    return text
        .toString()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .trim()
        .replace(/\s+/g, '-')
        .replace(/[^\w-]+/g, '')
        .replace(/--+/g, '-');
}

/**
 * Valide si une chaîne est un email valide
 * @param {String} email - Email à valider
 * @returns {Boolean} Vrai si valide
 */
function isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

/**
 * Valide si une chaîne est un numéro de téléphone français valide
 * @param {String} phone - Téléphone à valider
 * @returns {Boolean} Vrai si valide
 */
function isValidPhone(phone) {
    const regex = /^(0|\+33)[1-9]([-. ]?[0-9]{2}){4}$/;
    return regex.test(phone);
}

/**
 * Calcule la somme des valeurs d'une propriété dans un tableau d'objets
 * @param {Array} array - Tableau d'objets
 * @param {String} property - Propriété à additionner
 * @returns {Number} Somme des valeurs
 */
function sumBy(array, property) {
    return array.reduce((sum, item) => sum + (parseFloat(item[property]) || 0), 0);
}

/**
 * Compare deux objets pour voir s'ils sont égaux (comparaison superficielle)
 * @param {Object} obj1 - Premier objet
 * @param {Object} obj2 - Second objet
 * @returns {Boolean} Vrai si égaux
 */
function shallowEqual(obj1, obj2) {
    const keys1 = Object.keys(obj1);
    const keys2 = Object.keys(obj2);
    
    if (keys1.length !== keys2.length) {
        return false;
    }
    
    return keys1.every(key => obj1[key] === obj2[key]);
}

/**
 * Filtre les objets d'un tableau en fonction d'une requête de recherche
 * @param {Array} items - Tableau d'objets à filtrer
 * @param {String} query - Requête de recherche
 * @param {Array} fields - Champs à considérer pour la recherche
 * @returns {Array} Éléments filtrés
 */
function filterItems(items, query, fields) {
    if (!query || query.trim() === '') {
        return items;
    }
    
    const lowercaseQuery = query.toLowerCase();
    
    return items.filter(item => {
        return fields.some(field => {
            const value = item[field];
            if (!value) return false;
            return String(value).toLowerCase().includes(lowercaseQuery);
        });
    });
}

// Exporter les fonctions pour une utilisation dans d'autres fichiers
window.utils = {
    getRandomColor,
    getInitials,
    getScoreClass,
    formatNumber,
    truncateText,
    slugify,
    isValidEmail,
    isValidPhone,
    sumBy,
    shallowEqual,
    filterItems
};