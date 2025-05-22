# utils/company_matcher.py - Version corrigée avec matching basé sur les données réelles

import re
import json
from difflib import SequenceMatcher

def match_companies(companies, criteria):
    """
    Trouve les entreprises qui correspondent le mieux aux critères avec scoring réel
    """
    print(f"=== MATCHING ENTREPRISES ===")
    print(f"Entreprises à analyser: {len(companies)}")
    print(f"Critères reçus: {len(criteria)}")
    
    # Filtrer les critères sélectionnés
    selected_criteria = [c for c in criteria if c.get('selected', True)]
    print(f"Critères sélectionnés: {len(selected_criteria)}")
    
    if not selected_criteria:
        # Si aucun critère, retourner toutes les entreprises avec score de base
        return [{'score': 80, 'matchDetails': {}, **company} for company in companies]
    
    matched_companies = []
    
    for company in companies:
        try:
            # Calculer le score total pour cette entreprise
            total_score = 0
            match_details = {}
            
            for criterion in selected_criteria:
                criterion_score = calculate_advanced_criterion_score(company, criterion)
                match_details[criterion['name']] = criterion_score
                total_score += criterion_score
            
            # Score moyen
            average_score = round(total_score / len(selected_criteria)) if selected_criteria else 50
            
            # Bonus pour entreprises avec historique de projets similaires
            historical_bonus = calculate_historical_bonus(company)
            final_score = min(100, average_score + historical_bonus)
            
            matched_company = {
                **company,
                'score': final_score,
                'matchDetails': match_details,
                'selected': True
            }
            
            matched_companies.append(matched_company)
            
        except Exception as e:
            print(f"Erreur matching entreprise {company.get('name', 'Unknown')}: {e}")
            # En cas d'erreur, ajouter avec un score par défaut
            matched_companies.append({
                **company,
                'score': 50,
                'matchDetails': {'Erreur': 'Calcul impossible'},
                'selected': True
            })
    
    # Trier par score décroissant
    matched_companies.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"Entreprises matchées: {len(matched_companies)}")
    if matched_companies:
        print(f"Meilleur score: {matched_companies[0]['score']}% ({matched_companies[0]['name']})")
        print(f"Score moyen: {sum(c['score'] for c in matched_companies) / len(matched_companies):.1f}%")
    
    return matched_companies

def calculate_advanced_criterion_score(company, criterion):
    """
    Calcule un score avancé basé sur les données réelles de l'entreprise
    """
    criterion_name = criterion['name'].lower()
    criterion_desc = criterion.get('description', '').lower()
    
    # Analyse par type de critère
    if any(word in criterion_name for word in ['certification', 'mase', 'iso', 'qualibat']):
        return match_certification_advanced(company, criterion)
    
    elif any(word in criterion_name for word in ['expérience', 'projet', 'référence', 'historique']):
        return match_experience_advanced(company, criterion)
    
    elif any(word in criterion_name for word in ['zone', 'région', 'localisation', 'géographique']):
        return match_geographic_advanced(company, criterion)
    
    elif any(word in criterion_name for word in ['capacité', 'taille', 'effectif', 'ca', 'chiffre']):
        return match_capacity_advanced(company, criterion)
    
    elif any(word in criterion_name for word in ['domaine', 'activité', 'spécialité', 'métier']):
        return match_domain_advanced(company, criterion)
    
    elif any(word in criterion_name for word in ['technique', 'technologique', 'compétence']):
        return match_technical_advanced(company, criterion)
    
    else:
        return match_generic_advanced(company, criterion)

def match_certification_advanced(company, criterion):
    """Matching avancé des certifications"""
    if not company.get('certifications'):
        return 0
    
    criterion_name = criterion['name'].lower()
    criterion_desc = criterion.get('description', '').lower()
    company_certs = [cert.lower() for cert in company['certifications']]
    
    # Scores par certification
    cert_scores = {
        'mase': 100 if any('mase' in cert for cert in company_certs) else 0,
        'iso 9001': 90 if any('iso 9001' in cert or 'iso9001' in cert for cert in company_certs) else 0,
        'iso 14001': 85 if any('iso 14001' in cert or 'iso14001' in cert for cert in company_certs) else 0,
        'qualibat': 80 if any('qualibat' in cert for cert in company_certs) else 0,
        'cefri': 95 if any('cefri' in cert for cert in company_certs) else 0
    }
    
    # Vérifier la certification spécifique demandée
    for cert_type, score in cert_scores.items():
        if cert_type in criterion_name or cert_type in criterion_desc:
            return score
    
    # Score générique si l'entreprise a des certifications
    if company_certs:
        return min(85, len(company_certs) * 25)
    
    return 0

def match_experience_advanced(company, criterion):
    """Matching avancé de l'expérience"""
    experience_score = 0
    
    # Analyser l'expérience textuelle
    experience_text = company.get('experience', '').lower()
    if experience_text and experience_text != 'non spécifié':
        if len(experience_text) > 50:
            experience_score += 40
        elif len(experience_text) > 20:
            experience_score += 20
    
    # Analyser les lots/marchés historiques
    lots_marches = company.get('lots_marches', [])
    if lots_marches:
        experience_score += min(40, len(lots_marches) * 10)
        
        # Bonus pour projets similaires
        criterion_terms = extract_technical_terms(criterion.get('description', ''))
        for lot in lots_marches:
            lot_desc = lot.get('description', '').lower()
            similarity = calculate_text_similarity(criterion_terms, lot_desc)
            if similarity > 0.3:
                experience_score += 20 * similarity
    
    # Analyser le domaine d'activité
    domain = company.get('domain', '')
    if domain and domain != 'Autre':
        experience_score += 20
    
    return min(100, int(experience_score))

def match_geographic_advanced(company, criterion):
    """Matching avancé géographique"""
    company_location = company.get('location', '').lower()
    
    if not company_location or company_location == 'non spécifié':
        return 30  # Score neutre
    
    criterion_desc = criterion.get('description', '').lower()
    criterion_name = criterion['name'].lower()
    
    # Extraire les zones mentionnées dans le critère
    regions_france = {
        'ile-de-france': ['paris', 'idf', 'île-de-france', 'ile de france', '75', '77', '78', '91', '92', '93', '94', '95'],
        'nord': ['nord', 'hauts-de-france', 'lille', '59', '62', '02', '60', '80'],
        'est': ['est', 'grand est', 'strasbourg', 'metz', 'reims', '67', '68', '54', '55', '57', '88', '08', '10', '51', '52'],
        'ouest': ['ouest', 'bretagne', 'pays de la loire', 'normandie', '22', '29', '35', '56', '44', '49', '53', '72', '85', '14', '50', '61'],
        'sud': ['sud', 'paca', 'occitanie', 'marseille', 'toulouse', 'nice', '13', '83', '84', '04', '05', '06', '31', '65', '81', '82'],
        'centre': ['centre', 'orleans', 'tours', 'bourges', '18', '28', '36', '37', '41', '45'],
        'chooz': ['chooz', 'ardennes', '08', 'charleville']  # Spécifique au projet
    }
    
    # Vérifier la correspondance géographique
    for region, keywords in regions_france.items():
        region_mentioned = region in criterion_desc or region in criterion_name
        location_matches = any(keyword in company_location for keyword in keywords)
        
        if region_mentioned and location_matches:
            return 100
        elif location_matches and any(keyword in criterion_desc for keyword in keywords):
            return 90
    
    # National ou multi-régional
    if any(term in company_location for term in ['national', 'france', 'multi']):
        return 85
    
    # Score basé sur la proximité textuelle
    similarity = calculate_text_similarity(criterion_desc, company_location)
    return min(80, int(similarity * 100))

def match_capacity_advanced(company, criterion):
    """Matching avancé de la capacité"""
    capacity_score = 0
    
    # Analyser le chiffre d'affaires
    ca = company.get('ca', 'Non spécifié')
    if ca != 'Non spécifié':
        ca_score = analyze_ca_for_capacity(ca)
        capacity_score += ca_score * 0.6  # 60% du score
    
    # Analyser les effectifs
    employees = company.get('employees', 'Non spécifié')
    if employees != 'Non spécifié':
        emp_score = analyze_employees_for_capacity(employees)
        capacity_score += emp_score * 0.4  # 40% du score
    
    # Bonus pour historique de projets
    lots_marches = company.get('lots_marches', [])
    if len(lots_marches) > 0:
        capacity_score += min(20, len(lots_marches) * 5)
    
    return min(100, int(capacity_score))

def match_domain_advanced(company, criterion):
    """Matching avancé du domaine d'activité"""
    company_domain = company.get('domain', 'Autre').lower()
    criterion_desc = criterion.get('description', '').lower()
    criterion_name = criterion['name'].lower()
    
    # Correspondance exacte du domaine
    domain_mapping = {
        'électricité': ['electr', 'élec', 'energie', 'énergie', 'installation'],
        'mécanique': ['mecani', 'mécan', 'usinage', 'machine', 'moteur'],
        'hydraulique': ['hydraul', 'eau', 'fluide', 'tuyau', 'échangeur'],
        'bâtiment': ['batiment', 'bâtiment', 'construction', 'btp'],
        'maintenance': ['maintenance', 'entretien', 'service', 'réparation']
    }
    
    # Score de base selon le domaine
    base_scores = {
        'électricité': 85,
        'mécanique': 80,
        'hydraulique': 90,  # Bonus pour le projet échangeurs
        'bâtiment': 75,
        'maintenance': 95,  # Très pertinent pour maintenance
        'autre': 40
    }
    
    base_score = base_scores.get(company_domain, 40)
    
    # Vérifier la correspondance avec le critère
    if company_domain in domain_mapping:
        domain_keywords = domain_mapping[company_domain]
        for keyword in domain_keywords:
            if keyword in criterion_desc or keyword in criterion_name:
                return min(100, base_score + 15)
    
    # Analyser les lots pour correspondance technique
    lots_marches = company.get('lots_marches', [])
    if lots_marches:
        for lot in lots_marches:
            lot_desc = lot.get('description', '').lower()
            similarity = calculate_text_similarity(criterion_desc, lot_desc)
            if similarity > 0.4:
                return min(100, base_score + int(similarity * 30))
    
    return base_score

def match_technical_advanced(company, criterion):
    """Matching avancé des compétences techniques"""
    technical_score = 0
    
    # Analyser le domaine technique
    domain_score = match_domain_advanced(company, criterion)
    technical_score += domain_score * 0.5
    
    # Analyser l'expérience technique
    experience_score = match_experience_advanced(company, criterion)
    technical_score += experience_score * 0.3
    
    # Analyser les certifications techniques
    cert_score = match_certification_advanced(company, criterion)
    technical_score += cert_score * 0.2
    
    return min(100, int(technical_score))

def match_generic_advanced(company, criterion):
    """Matching générique avec analyse contextuelle"""
    criterion_text = (criterion['name'] + ' ' + criterion.get('description', '')).lower()
    
    # Construire le profil textuel de l'entreprise
    company_profile = build_company_text_profile(company)
    
    # Calculer la similarité
    similarity = calculate_text_similarity(criterion_text, company_profile)
    
    # Score de base selon la qualité des données
    data_quality_score = assess_company_data_quality(company)
    
    # Combiner les scores
    final_score = (similarity * 70) + (data_quality_score * 30)
    
    return min(100, int(final_score))

def calculate_historical_bonus(company):
    """Calcule un bonus basé sur l'historique de l'entreprise"""
    bonus = 0
    
    # Bonus pour les lots/marchés
    lots_marches = company.get('lots_marches', [])
    if lots_marches:
        bonus += min(15, len(lots_marches) * 3)
    
    # Bonus pour l'expérience documentée
    experience = company.get('experience', '')
    if experience and len(experience) > 50:
        bonus += 10
    
    # Bonus pour les certifications
    certifications = company.get('certifications', [])
    if certifications:
        bonus += min(10, len(certifications) * 3)
    
    # Bonus pour domaine spécialisé
    domain = company.get('domain', 'Autre')
    if domain != 'Autre':
        bonus += 5
    
    return min(20, bonus)

def extract_technical_terms(text):
    """Extrait les termes techniques d'un texte"""
    if not text:
        return ""
    
    technical_words = []
    words = re.findall(r'\b\w+\b', text.lower())
    
    for word in words:
        if len(word) > 4 and word not in ['pour', 'avec', 'dans', 'cette', 'sont']:
            technical_words.append(word)
    
    return ' '.join(technical_words)

def calculate_text_similarity(text1, text2):
    """Calcule la similarité entre deux textes"""
    if not text1 or not text2:
        return 0
    
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def analyze_ca_for_capacity(ca_str):
    """Analyse le chiffre d'affaires pour évaluer la capacité"""
    if not ca_str or ca_str == 'Non spécifié':
        return 50
    
    # Extraire le montant numérique
    ca_lower = ca_str.lower()
    
    try:
        if 'm€' in ca_lower or 'millions' in ca_lower:
            # Millions d'euros
            amount_match = re.search(r'(\d+(?:[.,]\d+)?)', ca_str)
            if amount_match:
                amount = float(amount_match.group(1).replace(',', '.'))
                if amount >= 10:
                    return 100
                elif amount >= 5:
                    return 90
                elif amount >= 2:
                    return 80
                elif amount >= 1:
                    return 70
                else:
                    return 60
        
        elif 'k€' in ca_lower or 'mille' in ca_lower:
            # Milliers d'euros
            amount_match = re.search(r'(\d+)', ca_str)
            if amount_match:
                amount = int(amount_match.group(1))
                if amount >= 2000:
                    return 85
                elif amount >= 1000:
                    return 75
                elif amount >= 500:
                    return 65
                else:
                    return 55
    
    except (ValueError, AttributeError):
        pass
    
    return 60  # Score neutre si analyse impossible

def analyze_employees_for_capacity(emp_str):
    """Analyse les effectifs pour évaluer la capacité"""
    if not emp_str or emp_str == 'Non spécifié':
        return 50
    
    try:
        # Extraire le nombre d'employés
        emp_match = re.search(r'(\d+)', str(emp_str))
        if emp_match:
            emp_count = int(emp_match.group(1))
            
            if emp_count >= 100:
                return 100
            elif emp_count >= 50:
                return 90
            elif emp_count >= 25:
                return 80
            elif emp_count >= 10:
                return 70
            elif emp_count >= 5:
                return 60
            else:
                return 50
    
    except (ValueError, AttributeError):
        pass
    
    return 55  # Score neutre

def build_company_text_profile(company):
    """Construit un profil textuel de l'entreprise"""
    profile_parts = []
    
    # Nom et domaine
    profile_parts.append(company.get('name', ''))
    profile_parts.append(company.get('domain', ''))
    
    # Localisation
    profile_parts.append(company.get('location', ''))
    
    # Expérience
    experience = company.get('experience', '')
    if experience != 'Non spécifié':
        profile_parts.append(experience)
    
    # Lots et marchés
    lots_marches = company.get('lots_marches', [])
    for lot in lots_marches:
        profile_parts.append(lot.get('description', ''))
    
    # Certifications
    certifications = company.get('certifications', [])
    profile_parts.extend(certifications)
    
    return ' '.join(profile_parts).lower()

def assess_company_data_quality(company):
    """Évalue la qualité des données de l'entreprise"""
    score = 0
    
    # Données de base
    if company.get('name'):
        score += 20
    if company.get('location') and company['location'] != 'Non spécifié':
        score += 15
    if company.get('domain') and company['domain'] != 'Autre':
        score += 15
    
    # Données détaillées
    if company.get('certifications'):
        score += 15
    if company.get('experience') and company['experience'] != 'Non spécifié':
        score += 15
    if company.get('lots_marches'):
        score += 10
    if company.get('contact'):
        score += 10
    
    return score