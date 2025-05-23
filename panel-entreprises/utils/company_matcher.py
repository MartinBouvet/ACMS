"""
company_matcher.py - Enhanced Matching Algorithm for EDF Panel Entreprises
"""

import re
import json
import logging
from difflib import SequenceMatcher

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def match_companies(companies, criteria, max_results=10, min_score=60):
    """
    Advanced matching algorithm that finds companies matching the specified criteria
    with detailed scoring and transparency
    
    Args:
        companies: List of company objects
        criteria: List of criteria objects with {id, name, description, selected} structure
        max_results: Maximum number of results to return
        min_score: Minimum score threshold for inclusion in results
        
    Returns:
        List of company objects with match scores and details
    """
    logger.info("=== COMPANY MATCHING PROCESS ===")
    logger.info(f"Companies to analyze: {len(companies)}")
    logger.info(f"Criteria received: {len(criteria)}")
    
    # Filter only selected criteria
    selected_criteria = [c for c in criteria if c.get('selected', True)]
    logger.info(f"Selected criteria: {len(selected_criteria)}")
    
    if not selected_criteria:
        logger.warning("No criteria selected, returning companies with default scores")
        return sorted_companies_by_relevance(companies, max_results)
    
    # Analyze criteria types for better matching strategy
    criteria_types = analyze_criteria_types(selected_criteria)
    logger.info(f"Criteria types identified: {criteria_types}")
    
    matched_companies = []
    
    for company in companies:
        try:
            company_scores = {}
            total_score = 0
            weights_sum = 0
            
            # Calculate scores for each criterion with appropriate weights
            for criterion in selected_criteria:
                weight = get_criterion_weight(criterion, criteria_types)
                criterion_score = calculate_criterion_score(company, criterion, criteria_types)
                
                company_scores[criterion['name']] = criterion_score
                total_score += criterion_score * weight
                weights_sum += weight
            
            # Calculate final weighted score
            final_score = round(total_score / weights_sum) if weights_sum > 0 else 50
            
            # Add historical and strategic bonuses
            bonuses = calculate_company_bonuses(company)
            final_score = min(100, final_score + bonuses)
            
            # Store the matched company with scores
            matched_company = {
                **company,
                'score': final_score,
                'matchDetails': company_scores,
                'selected': True  # Default to selected for convenience
            }
            
            matched_companies.append(matched_company)
            
        except Exception as e:
            logger.error(f"Error matching company {company.get('name', 'Unknown')}: {e}")
            matched_companies.append({
                **company,
                'score': 50,
                'matchDetails': {'Error': 'Calculation failed'},
                'selected': False
            })
    
    # Sort and filter results
    result = filter_and_sort_matches(matched_companies, min_score, max_results)
    
    logger.info(f"=== MATCHING COMPLETE ===")
    logger.info(f"Companies matched: {len(result)}")
    if result:
        logger.info(f"Top match: {result[0]['name']} ({result[0]['score']}%)")
        logger.info(f"Score range: {result[-1]['score']}% - {result[0]['score']}%")
    
    return result

def analyze_criteria_types(criteria):
    """
    Analyze and categorize criteria for better matching strategy
    """
    criteria_types = {
        'certification': [],
        'geographic': [],
        'technical': [],
        'experience': [],
        'domain': [],
        'capacity': [],
        'other': []
    }
    
    for criterion in criteria:
        criterion_name = criterion['name'].lower()
        criterion_desc = criterion.get('description', '').lower()
        
        # Categorize by keywords in name and description
        if any(word in criterion_name for word in ['certification', 'certif', 'mase', 'iso', 'qualif']):
            criteria_types['certification'].append(criterion['id'])
        elif any(word in criterion_name for word in ['zone', 'région', 'localisation', 'géographique', 'proximité']):
            criteria_types['geographic'].append(criterion['id'])
        elif any(word in criterion_name for word in ['technique', 'technologique', 'compétence', 'savoir']):
            criteria_types['technical'].append(criterion['id'])
        elif any(word in criterion_name for word in ['expérience', 'référence', 'projet', 'réalisation']):
            criteria_types['experience'].append(criterion['id'])
        elif any(word in criterion_name for word in ['domaine', 'activité', 'spécialité', 'métier']):
            criteria_types['domain'].append(criterion['id'])
        elif any(word in criterion_name for word in ['capacité', 'taille', 'effectif', 'ca', 'chiffre']):
            criteria_types['capacity'].append(criterion['id'])
        else:
            criteria_types['other'].append(criterion['id'])
    
    return criteria_types

def get_criterion_weight(criterion, criteria_types):
    """
    Determine the weight of a criterion based on its type and importance
    """
    criterion_id = criterion['id']
    
    # Base weights by category
    weights = {
        'certification': 1.0,  # Certifications are mandatory requirements
        'geographic': 0.8,     # Geographic proximity is important
        'technical': 1.2,      # Technical capabilities are critical
        'experience': 1.0,     # Experience is important
        'domain': 1.5,         # Domain expertise is very important
        'capacity': 0.7,       # Capacity is helpful but not critical
        'other': 0.5           # Other criteria get default weight
    }
    
    # Find which category this criterion belongs to
    for category, ids in criteria_types.items():
        if criterion_id in ids:
            return weights[category]
    
    return 1.0  # Default weight

def calculate_criterion_score(company, criterion, criteria_types):
    """
    Calculate how well a company matches a specific criterion
    """
    criterion_id = criterion['id']
    criterion_name = criterion['name'].lower()
    criterion_desc = criterion.get('description', '').lower()
    
    # Determine which matcher to use based on criterion type
    for category, ids in criteria_types.items():
        if criterion_id in ids:
            if category == 'certification':
                return match_certification(company, criterion)
            elif category == 'geographic':
                return match_geographic(company, criterion)
            elif category == 'technical':
                return match_technical(company, criterion)
            elif category == 'experience':
                return match_experience(company, criterion)
            elif category == 'domain':
                return match_domain(company, criterion)
            elif category == 'capacity':
                return match_capacity(company, criterion)
    
    # Default matching for other types
    return match_generic(company, criterion)

def match_certification(company, criterion):
    """
    Match company against certification criteria
    """
    company_certs = [cert.lower() for cert in company.get('certifications', [])]
    if not company_certs:
        return 0
    
    criterion_name = criterion['name'].lower()
    criterion_desc = criterion.get('description', '').lower()
    
    # Check for specific certifications mentioned
    cert_matches = {
        'mase': ('mase' in criterion_name or 'mase' in criterion_desc, 
                 any('mase' in cert for cert in company_certs)),
        
        'iso 9001': ('iso 9001' in criterion_name or 'iso 9001' in criterion_desc or 
                     ('iso' in criterion_name and 'qualité' in criterion_desc),
                     any('iso 9001' in cert.lower() for cert in company_certs)),
        
        'iso 14001': ('iso 14001' in criterion_name or 'iso 14001' in criterion_desc or
                      ('iso' in criterion_name and 'environnement' in criterion_desc),
                      any('iso 14001' in cert.lower() for cert in company_certs)),
        
        'cefri': ('cefri' in criterion_name or 'cefri' in criterion_desc or
                  ('nucléaire' in criterion_desc and 'certification' in criterion_name),
                  any('cefri' in cert.lower() for cert in company_certs))
    }
    
    # Check exact certification matches
    for cert_name, (is_required, is_present) in cert_matches.items():
        if is_required:
            return 100 if is_present else 0
    
    # If just looking for "certifications" in general
    if 'certification' in criterion_name and not any(cert in criterion_name for cert in ['mase', 'iso', 'cefri']):
        return min(90, len(company_certs) * 30)  # Score based on number of certifications
    
    # If we got here, company has certifications but not exactly what's requested
    return 50  # Partial match

def match_geographic(company, criterion):
    """
    Match company against geographic criteria
    """
    company_location = company.get('location', '').lower()
    company_geo_zone = company.get('geo_zone', 'Non spécifié').lower()
    
    if company_location == 'non spécifié' and company_geo_zone == 'non spécifié':
        return 0
    
    criterion_name = criterion['name'].lower()
    criterion_desc = criterion.get('description', '').lower()
    
    # Extract regions mentioned in criterion
    regions_mentioned = []
    
    regions = {
        'ile-de-france': ['ile-de-france', 'idf', 'paris', 'region parisienne'],
        'nord': ['nord', 'hauts-de-france', 'nord-pas-de-calais', 'picardie'],
        'est': ['est', 'grand est', 'alsace', 'lorraine', 'champagne'],
        'ardennes': ['ardennes', 'charleville', 'sedan', 'chooz'],  # Special for Chooz
        'ouest': ['ouest', 'bretagne', 'normandie', 'pays de loire'],
        'sud-ouest': ['sud-ouest', 'nouvelle aquitaine', 'aquitaine', 'occitanie'],
        'sud-est': ['sud-est', 'paca', 'rhone alpes', 'provence', 'alpes', 'cote d\'azur'],
        'centre': ['centre', 'val de loire', 'auvergne', 'limousin', 'bourgogne']
    }
    
    # Find mentioned regions
    for region, keywords in regions.items():
        if any(keyword in criterion_name or keyword in criterion_desc for keyword in keywords):
            regions_mentioned.append(region)
    
    # Special case for Chooz nuclear plant
    if 'chooz' in criterion_name or 'chooz' in criterion_desc:
        regions_mentioned.append('ardennes')
    
    # If specific regions are mentioned
    if regions_mentioned:
        # Check if company is in one of these regions
        for region in regions_mentioned:
            if region in company_location or region in company_geo_zone:
                return 100
            
            # Check for region keywords in company location
            region_keywords = regions.get(region, [])
            if any(keyword in company_location for keyword in region_keywords):
                return 100
        
        # Company not in mentioned regions but might be in nearby area
        # For example, if Est is mentioned and company is in Ile-de-France
        neighboring_regions = {
            'ile-de-france': ['est', 'nord', 'centre'],
            'nord': ['ile-de-france', 'est'],
            'est': ['ile-de-france', 'centre', 'nord'],
            'ardennes': ['est', 'nord'],
            'ouest': ['ile-de-france', 'centre', 'sud-ouest'],
            'sud-ouest': ['centre', 'ouest', 'sud-est'],
            'sud-est': ['centre', 'sud-ouest'],
            'centre': ['ile-de-france', 'est', 'ouest', 'sud-est', 'sud-ouest']
        }
        
        for region in regions_mentioned:
            neighbors = neighboring_regions.get(region, [])
            if any(neighbor in company_geo_zone.lower() for neighbor in neighbors):
                return 70  # Partial match for neighboring region
        
        # National company can still serve the region
        if 'france' in company_geo_zone.lower() or 'national' in company_location:
            return 60
        
        return 0  # Not in the requested region
    
    # If no specific region mentioned, assume national scope
    return 80

def match_technical(company, criterion):
    """
    Match company against technical criteria
    """
    criterion_name = criterion['name'].lower()
    criterion_desc = criterion.get('description', '').lower()
    
    score = 0
    
    # Check domain expertise first (most important for technical capability)
    domain_score = match_domain(company, criterion)
    score += domain_score * 0.4  # 40% weight
    
    # Check experience and capabilities
    experience = company.get('experience', '').lower()
    if experience != 'non spécifié':
        text_similarity = calculate_text_similarity(criterion_desc, experience)
        experience_score = int(text_similarity * 100)
        score += experience_score * 0.3  # 30% weight
    
    # Check contract history
    contracts = company.get('lots_marches', [])
    if contracts:
        max_contract_score = 0
        for contract in contracts:
            contract_desc = contract.get('description', '').lower()
            text_similarity = calculate_text_similarity(criterion_desc, contract_desc)
            contract_score = int(text_similarity * 100)
            max_contract_score = max(max_contract_score, contract_score)
        
        score += max_contract_score * 0.3  # 30% weight
    
    # Check specific capabilities
    capabilities = company.get('capabilities', [])
    if capabilities:
        max_capability_score = 0
        for capability in capabilities:
            text_similarity = calculate_text_similarity(criterion_desc, capability.lower())
            capability_score = int(text_similarity * 100)
            max_capability_score = max(max_capability_score, capability_score)
        
        # Add bonus for explicit capabilities
        score += min(20, max_capability_score * 0.2)  # Up to 20% bonus
    
    return min(100, int(score))

def match_experience(company, criterion):
    """
    Match company against experience criteria
    """
    criterion_name = criterion['name'].lower()
    criterion_desc = criterion.get('description', '').lower()
    
    experience_score = 0
    
    # Check formal experience description
    company_experience = company.get('experience', '').lower()
    if company_experience != 'non spécifié':
        text_similarity = calculate_text_similarity(criterion_desc, company_experience)
        experience_score += int(text_similarity * 60)  # Up to 60 points for experience text
    
    # Check contract history
    contracts = company.get('lots_marches', [])
    if contracts:
        # More contracts = more experience
        contracts_score = min(30, len(contracts) * 10)  # Up to 30 points for contract count
        experience_score += contracts_score
        
        # Check for contracts similar to the criterion
        max_contract_score = 0
        for contract in contracts:
            contract_desc = contract.get('description', '').lower()
            text_similarity = calculate_text_similarity(criterion_desc, contract_desc)
            contract_score = int(text_similarity * 40)  # Up to 40 points for relevant contracts
            max_contract_score = max(max_contract_score, contract_score)
        
        experience_score += max_contract_score
    
    # Check if keywords from criterion match company keywords
    company_keywords = company.get('keywords', [])
    if company_keywords:
        criterion_words = extract_significant_words(criterion_desc)
        matching_keywords = [word for word in criterion_words if word in company_keywords]
        keyword_score = min(20, len(matching_keywords) * 5)  # Up to 20 points for matching keywords
        experience_score += keyword_score
    
    return min(100, experience_score)

def match_domain(company, criterion):
    """
    Match company against domain criteria
    """
    company_domain = company.get('domain', 'Autre').lower()
    criterion_name = criterion['name'].lower()
    criterion_desc = criterion.get('description', '').lower()
    
    # Check for explicit domain mentions
    domain_keywords = {
        'électricité': ['électricité', 'electricite', 'électrique', 'electrique', 'courant', 'tension'],
        'mécanique': ['mécanique', 'mecanique', 'usinage', 'machines', 'pièces', 'pieces'],
        'hydraulique': ['hydraulique', 'fluide', 'eau', 'circuit', 'échangeur', 'echangeur'],
        'bâtiment': ['bâtiment', 'batiment', 'construction', 'btp', 'génie civil', 'genie civil'],
        'maintenance': ['maintenance', 'entretien', 'réparation', 'reparation', 'service']
    }
    
    # Find domains mentioned in criterion
    mentioned_domains = []
    for domain, keywords in domain_keywords.items():
        if any(keyword in criterion_name or keyword in criterion_desc for keyword in keywords):
            mentioned_domains.append(domain)
    
    # Exact match with mentioned domain
    if mentioned_domains and company_domain.lower() in mentioned_domains:
        return 100
    
    # Related domain
    related_domains = {
        'électricité': ['maintenance'],
        'mécanique': ['maintenance', 'hydraulique'],
        'hydraulique': ['mécanique', 'maintenance'],
        'bâtiment': ['maintenance'],
        'maintenance': ['électricité', 'mécanique', 'hydraulique', 'bâtiment']
    }
    
    if mentioned_domains:
        for mentioned_domain in mentioned_domains:
            related = related_domains.get(mentioned_domain, [])
            if company_domain.lower() in related:
                return 70  # Related domain
    
    # If no specific domain mentioned in criterion, check text similarity
    if not mentioned_domains:
        # Generic domain criteria, check keywords
        company_keywords = company.get('keywords', [])
        criterion_words = extract_significant_words(criterion_desc)
        matching_keywords = [word for word in criterion_words if word in company_keywords]
        
        if matching_keywords:
            return min(90, 50 + len(matching_keywords) * 10)
        
        # Check experience and capabilities
        experience = company.get('experience', '').lower()
        if experience != 'non spécifié':
            text_similarity = calculate_text_similarity(criterion_desc, experience)
            if text_similarity > 0.4:  # Good match in experience
                return int(text_similarity * 90)
    
    # Default domain score based on whether company has specified domain
    return 40 if company_domain != 'autre' else 20

def match_capacity(company, criterion):
    """
    Match company against capacity criteria (size, employees, CA)
    """
    criterion_name = criterion['name'].lower()
    criterion_desc = criterion.get('description', '').lower()
    
    capacity_score = 50  # Default middle score
    
    # Check employees
    employees = company.get('employees', 'Non spécifié')
    ca = company.get('ca', 'Non spécifié')
    
    # If criterion is specifically about size
    size_keywords = {
        'petite': ['petite', 'small', 'tpe', '<10', 'moins de 10'],
        'moyenne': ['moyenne', 'medium', 'pme', '10-50', 'entre 10 et 50'],
        'grande': ['grande', 'large', 'eti', '>50', 'plus de 50', 'importante']
    }
    
    # Check if criterion specifies company size
    size_requirement = None
    for size, keywords in size_keywords.items():
        if any(keyword in criterion_name or keyword in criterion_desc for keyword in keywords):
            size_requirement = size
            break
    
    if size_requirement:
        # Extract employee count
        emp_count = 0
        if employees != 'Non spécifié':
            emp_match = re.search(r'\d+', employees)
            if emp_match:
                emp_count = int(emp_match.group(0))
        
        # Match employee count with size requirement
        if size_requirement == 'petite':
            if emp_count > 0 and emp_count < 10:
                return 100
            elif emp_count >= 10 and emp_count <= 20:
                return 70
            elif emp_count > 20:
                return 30
        elif size_requirement == 'moyenne':
            if emp_count >= 10 and emp_count <= 50:
                return 100
            elif emp_count < 10:
                return 50
            elif emp_count > 50:
                return 70
        elif size_requirement == 'grande':
            if emp_count > 50:
                return 100
            elif emp_count >= 20:
                return 60
            else:
                return 30
    
    # Check CA requirements
    ca_keywords = {
        'petit': ['petit ca', 'petit chiffre', '<500k', 'moins de 500k'],
        'moyen': ['moyen ca', 'moyen chiffre', '500k-2m', 'entre 500k et 2m'],
        'grand': ['grand ca', 'grand chiffre', '>2m', 'plus de 2m']
    }
    
    ca_requirement = None
    for size, keywords in ca_keywords.items():
        if any(keyword in criterion_name or keyword in criterion_desc for keyword in keywords):
            ca_requirement = size
            break
    
    if ca_requirement:
        # Extract CA value
        ca_value = 0
        if ca != 'Non spécifié':
            ca_match = re.search(r'(\d+(?:[.,]\d+)?)', ca)
            if ca_match:
                ca_num = ca_match.group(1).replace(',', '.')
                if 'M€' in ca:
                    ca_value = float(ca_num) * 1000000
                elif 'k€' in ca:
                    ca_value = float(ca_num) * 1000
                else:
                    ca_value = float(ca_num)
        
        # Match CA with requirement
        if ca_requirement == 'petit':
            if ca_value > 0 and ca_value < 500000:
                return 100
            elif ca_value >= 500000 and ca_value <= 1000000:
                return 70
            elif ca_value > 1000000:
                return 40
        elif ca_requirement == 'moyen':
            if ca_value >= 500000 and ca_value <= 2000000:
                return 100
            elif ca_value < 500000:
                return 60
            elif ca_value > 2000000:
                return 80
        elif ca_requirement == 'grand':
            if ca_value > 2000000:
                return 100
            elif ca_value >= 1000000:
                return 70
            else:
                return 30
    
    # Generic capacity check
    if 'capacité' in criterion_name or 'capacite' in criterion_name:
        # Consider experience, employees and CA
        score = 0
        
        # More employees = higher capacity
        if employees != 'Non spécifié':
            emp_match = re.search(r'\d+', employees)
            if emp_match:
                emp_count = int(emp_match.group(0))
                if emp_count > 50:
                    score += 30
                elif emp_count > 20:
                    score += 25
                elif emp_count > 10:
                    score += 20
                else:
                    score += 10
        
        # Higher CA = higher capacity
        if ca != 'Non spécifié':
            ca_match = re.search(r'(\d+(?:[.,]\d+)?)', ca)
            if ca_match:
                ca_num = ca_match.group(1).replace(',', '.')
                if 'M€' in ca:
                    score += 30  # Millions of euros
                elif 'k€' in ca and float(ca_num) > 500:
                    score += 20  # Hundreds of thousands
                else:
                    score += 10
        
        # Contract history shows capacity
        contracts = company.get('lots_marches', [])
        if contracts:
            score += min(40, len(contracts) * 10)
        
        return min(100, score)
    
    return capacity_score

def match_generic(company, criterion):
    """
    Generic matching for criteria that don't fit specific categories
    """
    criterion_name = criterion['name'].lower()
    criterion_desc = criterion.get('description', '').lower()
    
    # Build company profile for matching
    company_profile = build_company_profile(company)
    
    # Calculate text similarity
    text_similarity = calculate_text_similarity(criterion_name + ' ' + criterion_desc, company_profile)
    
    # Convert to score
    similarity_score = int(text_similarity * 80)  # Up to 80 points for text similarity
    
    # Check if criterion keywords match company keywords
    company_keywords = company.get('keywords', [])
    criterion_words = extract_significant_words(criterion_desc)
    matching_keywords = [word for word in criterion_words if word in company_keywords]
    keyword_score = min(20, len(matching_keywords) * 5)  # Up to 20 points for matching keywords
    
    return min(100, similarity_score + keyword_score)

def build_company_profile(company):
    """
    Build a comprehensive text profile of the company for matching
    """
    profile_parts = []
    
    # Add name and domain
    profile_parts.append(company.get('name', ''))
    profile_parts.append(company.get('domain', ''))
    
    # Add certifications
    certifications = company.get('certifications', [])
    profile_parts.extend(certifications)
    
    # Add experience
    experience = company.get('experience', '')
    if experience != 'Non spécifié':
        profile_parts.append(experience)
    
    # Add contracts
    contracts = company.get('lots_marches', [])
    for contract in contracts:
        profile_parts.append(contract.get('description', ''))
    
    # Add capabilities
    capabilities = company.get('capabilities', [])
    profile_parts.extend(capabilities)
    
    # Add keywords
    keywords = company.get('keywords', [])
    profile_parts.extend(keywords)
    
    return ' '.join(profile_parts).lower()

def calculate_company_bonuses(company):
    """
    Calculate bonus points for company based on strategic factors
    """
    bonus = 0
    
    # Bonus for certifications (quality indicator)
    certifications = company.get('certifications', [])
    if certifications:
        cert_bonus = min(5, len(certifications) * 2)
        bonus += cert_bonus
    
    # Bonus for contract history (reliability indicator)
    contracts = company.get('lots_marches', [])
    if contracts:
        contract_bonus = min(10, len(contracts) * 2)
        bonus += contract_bonus
    
    # Bonus for complete company data (indicates active supplier)
    completeness = 0
    if company.get('domain', 'Autre') != 'Autre':
        completeness += 1
    if company.get('location', 'Non spécifié') != 'Non spécifié':
        completeness += 1
    if company.get('experience', 'Non spécifié') != 'Non spécifié':
        completeness += 1
    if company.get('ca', 'Non spécifié') != 'Non spécifié':
        completeness += 1
    if company.get('employees', 'Non spécifié') != 'Non spécifié':
        completeness += 1
    
    completeness_bonus = min(5, completeness)
    bonus += completeness_bonus
    
    return min(20, bonus)  # Cap total bonus at 20 points

def calculate_text_similarity(text1, text2):
    """
    Calculate semantic similarity between two texts
    """
    if not text1 or not text2:
        return 0
    
    # Clean and normalize texts
    text1 = re.sub(r'[^\w\s]', ' ', text1.lower())
    text2 = re.sub(r'[^\w\s]', ' ', text2.lower())
    
    # Extract significant words
    words1 = extract_significant_words(text1)
    words2 = extract_significant_words(text2)
    
    # Calculate Jaccard similarity for significant words
    common_words = set(words1).intersection(set(words2))
    all_words = set(words1).union(set(words2))
    
    if not all_words:
        return 0
    
    jaccard = len(common_words) / len(all_words)
    
    # Calculate sequence similarity (for word order)
    sequence = SequenceMatcher(None, text1, text2).ratio()
    
    # Return weighted average (more weight to Jaccard for semantic meaning)
    return (jaccard * 0.7) + (sequence * 0.3)

def extract_significant_words(text):
    """
    Extract significant words from text, removing common words
    """
    if not text:
        return []
    
    # Common French words to filter out
    stop_words = set([
        'le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'de', 'du', 'au', 'aux',
        'ce', 'cette', 'ces', 'mon', 'ton', 'son', 'notre', 'votre', 'leur',
        'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles',
        'a', 'à', 'en', 'par', 'pour', 'avec', 'sans', 'dans', 'sur', 'sous',
        'est', 'sont', 'sera', 'être', 'avoir', 'fait', 'faire', 'peut', 'doit',
        'plus', 'moins', 'très', 'peu', 'trop', 'tout', 'tous', 'toute', 'toutes',
        'qui', 'que', 'quoi', 'dont', 'où', 'quand', 'comment', 'pourquoi'
    ])
    
    # Extract words (at least 3 chars) and filter out stop words
    words = [word for word in re.findall(r'\b\w{3,}\b', text.lower()) 
             if word not in stop_words]
    
    return words

def filter_and_sort_matches(matches, min_score, max_results):
    """
    Filter and sort matches by score, applying diversity rules for better results
    """
    # First filter by minimum score
    qualified_matches = [m for m in matches if m['score'] >= min_score]
    
    # Sort by score
    sorted_matches = sorted(qualified_matches, key=lambda x: x['score'], reverse=True)
    
    # Apply diversity rules
    diverse_matches = apply_diversity_rules(sorted_matches, max_results)
    
    return diverse_matches[:max_results]

def apply_diversity_rules(matches, max_results):
    """
    Apply diversity rules to ensure a mix of different companies
    """
    if len(matches) <= max_results:
        return matches
    
    # First, take the top matches regardless of diversity
    top_matches = matches[:min(3, max_results // 2)]
    
    # Get remaining slots
    remaining_slots = max_results - len(top_matches)
    if remaining_slots <= 0:
        return top_matches
    
    # Remaining candidates
    candidates = matches[len(top_matches):]
    
    # Track domains we already have
    selected_domains = [m.get('domain', 'Autre') for m in top_matches]
    
    # Track regions we already have
    selected_regions = [m.get('geo_zone', 'Non spécifié') for m in top_matches]
    
    # Select diverse companies for remaining slots
    diverse_selections = []
    
    # First, try to get different domains
    for candidate in candidates:
        if len(diverse_selections) >= remaining_slots:
            break
            
        domain = candidate.get('domain', 'Autre')
        region = candidate.get('geo_zone', 'Non spécifié')
        
        # Prioritize companies with different domains and regions
        if domain not in selected_domains or region not in selected_regions:
            diverse_selections.append(candidate)
            selected_domains.append(domain)
            selected_regions.append(region)
    
    # If we still have slots, fill with top remaining
    remaining_slots = remaining_slots - len(diverse_selections)
    if remaining_slots > 0:
        for candidate in candidates:
            if candidate not in diverse_selections:
                diverse_selections.append(candidate)
                if len(diverse_selections) >= remaining_slots:
                    break
    
    return top_matches + diverse_selections

def sorted_companies_by_relevance(companies, max_results=10):
    """
    Sort companies by overall relevance when no specific criteria are provided
    """
    scored_companies = []
    
    for company in companies:
        # Base score
        base_score = 70
        
        # Bonuses for completeness
        completeness_bonus = 0
        
        if company.get('domain', 'Autre') != 'Autre':
            completeness_bonus += 2
        
        if company.get('certifications', []):
            completeness_bonus += len(company.get('certifications', [])) * 2
        
        if company.get('experience', 'Non spécifié') != 'Non spécifié':
            completeness_bonus += 5
        
        if company.get('lots_marches', []):
            completeness_bonus += min(10, len(company.get('lots_marches', [])) * 2)
        
        if company.get('ca', 'Non spécifié') != 'Non spécifié':
            completeness_bonus += 3
        
        if company.get('employees', 'Non spécifié') != 'Non spécifié':
            completeness_bonus += 3
        
        if company.get('contact', None):
            completeness_bonus += 2
        
        # Calculate final score
        final_score = min(100, base_score + completeness_bonus)
        
        # Add to results
        scored_companies.append({
            **company,
            'score': final_score,
            'matchDetails': {'Pertinence générale': final_score},
            'selected': True
        })
    
    # Sort and limit
    return sorted(scored_companies, key=lambda x: x['score'], reverse=True)[:max_results]