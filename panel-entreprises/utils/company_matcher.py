# Utility to match companies
# utils/company_matcher.py

def match_companies(companies, criteria):
    """
    Trouve les entreprises qui correspondent le mieux aux critères de sélection
    
    Args:
        companies: Liste des entreprises à évaluer
        criteria: Liste des critères de sélection
        
    Returns:
        Liste des entreprises correspondantes avec scores de match
    """
    # Ne conserver que les critères sélectionnés
    selected_criteria = [c for c in criteria if c.get('selected', True)]
    
    if not selected_criteria:
        # Si aucun critère n'est sélectionné, toutes les entreprises correspondent
        return [{'score': 100, 'matchDetails': {}, **company} for company in companies]
    
    matched_companies = []
    
    for company in companies:
        score = 0
        match_details = {}
        
        for criterion in selected_criteria:
            criterion_name = criterion['name'].lower()
            criterion_desc = criterion.get('description', '').lower()
            
            # Calculer le score pour ce critère
            criterion_score = calculate_criterion_score(company, criterion)
            
            # Stocker le détail du score
            match_details[criterion['name']] = criterion_score
            
            # Ajouter au score total
            score += criterion_score
        
        # Calculer le score moyen
        if selected_criteria:
            score = round(score / len(selected_criteria))
        
        matched_companies.append({
            **company,
            'score': score,
            'matchDetails': match_details
        })
    
    # Trier par score (du plus élevé au plus bas)
    matched_companies.sort(key=lambda x: x['score'], reverse=True)
    
    return matched_companies

def calculate_criterion_score(company, criterion):
    """
    Calcule le score de correspondance pour un critère spécifique
    
    Args:
        company: Données de l'entreprise
        criterion: Critère à évaluer
        
    Returns:
        Score entre 0 et 100
    """
    criterion_name = criterion['name'].lower()
    criterion_desc = criterion.get('description', '').lower()
    
    # Certification
    if 'certification' in criterion_name or 'mase' in criterion_name:
        return match_certification(company, criterion)
    
    # Expérience
    if 'expérience' in criterion_name or 'projet' in criterion_name:
        return match_experience(company, criterion)
    
    # Zone d'intervention
    if 'zone' in criterion_name or 'région' in criterion_name or 'localisation' in criterion_name:
        return match_zone(company, criterion)
    
    # Capacité / taille
    if 'capacité' in criterion_name or 'taille' in criterion_name or 'effectif' in criterion_name:
        return match_capacity(company, criterion)
    
    # Correspondance générique
    return match_generic(company, criterion)

def match_certification(company, criterion):
    """Évalue les certifications de l'entreprise"""
    if not company.get('certifications'):
        return 0
    
    criterion_desc = criterion.get('description', '').lower()
    certifications = [cert.lower() for cert in company['certifications']]
    
    # Vérifier si MASE est spécifiquement requis
    if 'mase' in criterion_name or 'mase' in criterion_desc:
        if any('mase' in cert for cert in certifications):
            return 100
        else:
            return 0
    
    # Vérifier ISO 9001
    if 'iso 9001' in criterion_desc or 'qualité' in criterion_desc:
        if any('iso 9001' in cert or 'iso9001' in cert for cert in certifications):
            return 100
        else:
            return 0
    
    # Vérifier ISO 14001
    if 'iso 14001' in criterion_desc or 'environnement' in criterion_desc:
        if any('iso 14001' in cert or 'iso14001' in cert for cert in certifications):
            return 100
        else:
            return 0
    
    # Si aucune certification spécifique n'est mentionnée, considérer que toute certification est bonne
    if certifications:
        return 100
    
    return 0

# utils/company_matcher.py

def match_companies(companies, criteria):
    """
    Trouve les entreprises qui correspondent le mieux aux critères de sélection
    
    Args:
        companies: Liste des entreprises à évaluer
        criteria: Liste des critères de sélection
        
    Returns:
        Liste des entreprises correspondantes avec scores de match
    """
    # Ne conserver que les critères sélectionnés
    selected_criteria = [c for c in criteria if c.get('selected', True)]
    
    if not selected_criteria:
        # Si aucun critère n'est sélectionné, toutes les entreprises correspondent
        return [{'score': 100, 'matchDetails': {}, **company} for company in companies]
    
    matched_companies = []
    
    for company in companies:
        score = 0
        match_details = {}
        
        for criterion in selected_criteria:
            criterion_name = criterion['name'].lower()
            criterion_desc = criterion.get('description', '').lower()
            
            # Calculer le score pour ce critère
            criterion_score = calculate_criterion_score(company, criterion)
            
            # Stocker le détail du score
            match_details[criterion['name']] = criterion_score
            
            # Ajouter au score total
            score += criterion_score
        
        # Calculer le score moyen
        if selected_criteria:
            score = round(score / len(selected_criteria))
        
        matched_companies.append({
            **company,
            'score': score,
            'matchDetails': match_details
        })
    
    # Trier par score (du plus élevé au plus bas)
    matched_companies.sort(key=lambda x: x['score'], reverse=True)
    
    return matched_companies

def calculate_criterion_score(company, criterion):
    """
    Calcule le score de correspondance pour un critère spécifique
    
    Args:
        company: Données de l'entreprise
        criterion: Critère à évaluer
        
    Returns:
        Score entre 0 et 100
    """
    criterion_name = criterion['name'].lower()
    criterion_desc = criterion.get('description', '').lower()
    
    # Certification
    if 'certification' in criterion_name or 'mase' in criterion_name:
        return match_certification(company, criterion)
    
    # Expérience
    if 'expérience' in criterion_name or 'projet' in criterion_name:
        return match_experience(company, criterion)
    
    # Zone d'intervention
    if 'zone' in criterion_name or 'région' in criterion_name or 'localisation' in criterion_name:
        return match_zone(company, criterion)
    
    # Capacité / taille
    if 'capacité' in criterion_name or 'taille' in criterion_name or 'effectif' in criterion_name:
        return match_capacity(company, criterion)
    
    # Correspondance générique
    return match_generic(company, criterion)

def match_certification(company, criterion):
    """Évalue les certifications de l'entreprise"""
    if not company.get('certifications'):
        return 0
    
    criterion_desc = criterion.get('description', '').lower()
    certifications = [cert.lower() for cert in company['certifications']]
    
    # Vérifier si MASE est spécifiquement requis
    if 'mase' in criterion_name or 'mase' in criterion_desc:
        if any('mase' in cert for cert in certifications):
            return 100
        else:
            return 0
    
    # Vérifier ISO 9001
    if 'iso 9001' in criterion_desc or 'qualité' in criterion_desc:
        if any('iso 9001' in cert or 'iso9001' in cert for cert in certifications):
            return 100
        else:
            return 0
    
    # Vérifier ISO 14001
    if 'iso 14001' in criterion_desc or 'environnement' in criterion_desc:
        if any('iso 14001' in cert or 'iso14001' in cert for cert in certifications):
            return 100
        else:
            return 0
    
    # Si aucune certification spécifique n'est mentionnée, considérer que toute certification est bonne
    if certifications:
        return 100
    
    return 0

def match_experience(company, criterion):
   """Évalue l'expérience de l'entreprise"""
   if not company.get('experience'):
       return 0
   
   experience = company['experience'].lower()
   criterion_desc = criterion.get('description', '').lower()
   
   # Vérifier si un nombre minimum de projets est mentionné
   min_projects_match = re.search(r'minimum\s+(\d+)\s+projets?', criterion_desc)
   if min_projects_match:
       min_projects = int(min_projects_match.group(1))
       
       # Chercher le nombre de projets dans l'expérience
       company_projects_match = re.search(r'(\d+)\s+projets?', experience)
       if company_projects_match:
           company_projects = int(company_projects_match.group(1))
           if company_projects >= min_projects:
               return 100
           else:
               # Score proportionnel
               return round((company_projects / min_projects) * 100)
   
   # Recherche de mots-clés d'expérience
   exp_keywords = ['projets similaires', 'expérience similaire', 'réalisations similaires']
   if any(keyword in experience for keyword in exp_keywords):
       return 100
   
   # Si on ne peut pas déterminer précisément
   if 'expérience' in experience or 'projet' in experience:
       return 70
   
   return 50

def match_zone(company, criterion):
   """Évalue la zone d'intervention de l'entreprise"""
   if not company.get('location'):
       return 0
   
   location = company['location'].lower()
   criterion_desc = criterion.get('description', '').lower()
   
   # Vérifier les départements sélectionnés
   if 'selectedDepartments' in criterion and criterion['selectedDepartments']:
       for dept in criterion['selectedDepartments']:
           dept_lower = dept.lower()
           
           # Extraire le code du département
           dept_code_match = re.search(r'(\d+)', dept_lower)
           if dept_code_match and dept_code_match.group(1) in location:
               return 100
           
           # Vérifier le nom du département
           dept_name = dept_lower.split('-')[-1].strip() if '-' in dept_lower else dept_lower
           if dept_name in location:
               return 100
       
       return 0  # Aucun département sélectionné ne correspond
   
   # Vérifier les régions
   regions = {
       'ile-de-france': ['paris', 'idf', 'île-de-france', 'ile de france'],
       'nord': ['nord', 'hauts-de-france', 'lille'],
       'est': ['est', 'grand est', 'strasbourg', 'alsace', 'lorraine'],
       'ouest': ['ouest', 'bretagne', 'pays de la loire', 'normandie'],
       'sud': ['sud', 'paca', 'occitanie', 'marseille', 'toulouse']
   }
   
   for region, keywords in regions.items():
       if any(keyword in criterion_desc for keyword in [region] + keywords):
           if any(keyword in location for keyword in keywords):
               return 100
   
   # National
   if 'national' in location or 'france entière' in location:
       return 100
   
   # Score partiel si on ne peut pas déterminer précisément
   return 50

def match_capacity(company, criterion):
   """Évalue la capacité ou taille de l'entreprise"""
   criterion_desc = criterion.get('description', '').lower()
   
   # Vérifier le nombre d'employés
   if company.get('employees'):
       try:
           # Extraire le nombre d'employés
           employees_str = company['employees']
           employees = int(''.join(filter(str.isdigit, employees_str)))
           
           # Chercher le minimum requis dans le critère
           min_employees_match = re.search(r'minimum\s+(\d+)\s+(?:salariés|employés|personnes)', criterion_desc)
           if min_employees_match:
               min_employees = int(min_employees_match.group(1))
               if employees >= min_employees:
                   return 100
               else:
                   # Score proportionnel
                   return min(100, round((employees / min_employees) * 100))
           
           # Sinon, score basé sur la taille
           if employees > 100:
               return 100
           elif employees > 50:
               return 90
           elif employees > 25:
               return 80
           elif employees > 10:
               return 70
           elif employees > 5:
               return 60
           else:
               return 50
       except (ValueError, TypeError):
           pass
   
   # Vérifier le chiffre d'affaires
   if company.get('ca'):
       ca_str = company['ca'].lower()
       
       try:
           # Extraire le montant du CA
           amount_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*([km])?€?', ca_str)
           if amount_match:
               amount = float(amount_match.group(1).replace(',', '.'))
               unit = amount_match.group(2)
               
               # Convertir en euros
               if unit == 'k':
                   amount *= 1000
               elif unit == 'm':
                   amount *= 1000000
               
               # Score basé sur le CA
               if amount > 10000000:  # > 10M€
                   return 100
               elif amount > 5000000:  # > 5M€
                   return 90
               elif amount > 1000000:  # > 1M€
                   return 80
               elif amount > 500000:   # > 500k€
                   return 70
               elif amount > 100000:   # > 100k€
                   return 60
               else:
                   return 50
       except (ValueError, TypeError):
           pass
   
   # Score par défaut si on ne peut pas évaluer
   return 50

def match_generic(company, criterion):
   """Matching générique pour les autres types de critères"""
   criterion_name = criterion['name'].lower()
   criterion_desc = criterion.get('description', '').lower()
   
   # Convertir les données de l'entreprise en texte pour chercher des correspondances
   company_str = json.dumps(company, ensure_ascii=False).lower()
   
   # Extraire les termes significatifs du critère
   terms = set()
   all_words = (criterion_name + ' ' + criterion_desc).split()
   
   # Filtrer les mots significatifs (plus de 3 caractères)
   for word in all_words:
       word = word.strip(',.;:!?()[]{}\'\"').lower()
       if len(word) > 3 and word not in ['pour', 'avec', 'dans', 'les', 'des', 'qui', 'est', 'sont', 'ont']:
           terms.add(word)
   
   if not terms:
       return 50  # Si pas de termes significatifs
   
   # Compter combien de termes sont trouvés dans les données de l'entreprise
   matches = sum(1 for term in terms if term in company_str)
   
   # Calculer le score
   return round((matches / len(terms)) * 100) if matches > 0 else 0