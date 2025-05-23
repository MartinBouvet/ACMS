"""
excel_parser.py - Enhanced Company Data Parser for EDF Panel Entreprises
"""

import pandas as pd
import os
import re
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_companies_from_excel(file_path):
    """
    Load companies from Excel file with enhanced domain and criteria extraction
    """
    try:
        logger.info(f"=== LOADING EXCEL FILE: {file_path} ===")
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return []
        
        # Load Excel file with proper engine
        xl_file = pd.ExcelFile(file_path, engine='openpyxl')
        logger.info(f"Available sheets: {xl_file.sheet_names}")
        
        # Find the main sheet with company data
        main_sheet = find_company_sheet(xl_file)
        if not main_sheet:
            main_sheet = xl_file.sheet_names[0]
            logger.info(f"Using first sheet as default: {main_sheet}")
        
        # Read the sheet into DataFrame
        df = pd.read_excel(file_path, sheet_name=main_sheet, engine='openpyxl')
        logger.info(f"DataFrame dimensions: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Clean column names
        df.columns = df.columns.astype(str).str.strip()
        
        # Find key columns for company data
        column_mapping = identify_columns(df)
        logger.info(f"Column mapping identified: {column_mapping}")
        
        # Process each row to extract company information
        companies = []
        skipped_rows = 0
        
        for idx, row in df.iterrows():
            try:
                # Extract company name first - skip if no valid name
                company_name = extract_company_name(row, column_mapping, df.columns)
                if not company_name or company_name.strip() == "":
                    skipped_rows += 1
                    continue
                
                # Create unique ID
                company_id = f"ENT_{str(len(companies) + 1).zfill(3)}"
                
                # Extract all company information
                company = {
                    'id': company_id,
                    'name': company_name,
                    'domain': extract_domain(row, column_mapping, df.columns),
                    'location': extract_location(row, column_mapping, df.columns),
                    'certifications': extract_certifications(row, column_mapping, df.columns),
                    'ca': extract_ca(row, column_mapping, df.columns),
                    'employees': extract_employees(row, column_mapping, df.columns),
                    'contact': extract_contact_info(row, column_mapping, df.columns),
                    'experience': extract_experience(row, column_mapping, df.columns),
                    'lots_marches': extract_contracts(row, column_mapping, df.columns),
                    'capabilities': extract_capabilities(row, column_mapping, df.columns),
                    'score': 0
                }
                
                companies.append(company)
                
            except Exception as e:
                logger.error(f"Error processing row {idx}: {e}")
                skipped_rows += 1
        
        logger.info(f"=== EXTRACTION RESULTS ===")
        logger.info(f"Companies extracted: {len(companies)}")
        logger.info(f"Rows skipped: {skipped_rows}")
        
        # Enrich with additional data (inferred domains, capabilities)
        enrich_company_data(companies)
        
        return companies
    
    except Exception as e:
        logger.error(f"Excel loading error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def find_company_sheet(xl_file):
    """Find the sheet most likely to contain company data"""
    company_keywords = ['entreprise', 'societe', 'société', 'fournisseur', 'prestataire', 'listing']
    
    # Check sheet names
    for sheet in xl_file.sheet_names:
        sheet_lower = sheet.lower()
        if any(keyword in sheet_lower for keyword in company_keywords):
            return sheet
    
    # If no match in names, check first row of each sheet
    for sheet in xl_file.sheet_names:
        try:
            # Read just the first row
            df_sample = pd.read_excel(xl_file, sheet_name=sheet, nrows=1)
            headers = ' '.join(str(col).lower() for col in df_sample.columns)
            
            # Check if company-related headers exist
            if any(keyword in headers for keyword in company_keywords):
                return sheet
        except:
            continue
    
    return None

def identify_columns(df):
    """Identify key columns in the DataFrame"""
    column_mapping = {
        'company_name': [],
        'domain': [],
        'location': [],
        'certifications': [],
        'ca': [],
        'employees': [],
        'email': [],
        'phone': [],
        'experience': [],
        'contracts': [],
        'capabilities': []
    }
    
    # Patterns for different column types
    patterns = {
        'company_name': ['nom', 'raison sociale', 'société', 'societe', 'entreprise', 'prestataire', 'titulaire'],
        'domain': ['domaine', 'activité', 'activite', 'métier', 'metier', 'spécialité', 'specialite', 'secteur'],
        'location': ['localisation', 'lieu', 'adresse', 'ville', 'commune', 'département', 'departement', 'région', 'region', 'code postal'],
        'certifications': ['certification', 'qualif', 'habilitation', 'norme', 'mase', 'iso'],
        'ca': ['ca', 'chiffre', 'affaire', 'revenu', 'turnover'],
        'employees': ['effectif', 'employé', 'employe', 'salarié', 'salarie', 'personnel'],
        'email': ['email', 'mail', 'courriel', 'contact'],
        'phone': ['téléphone', 'telephone', 'tel', 'contact', 'portable', 'mobile'],
        'experience': ['expérience', 'experience', 'référence', 'reference', 'antécédent', 'antecedent', 'historique'],
        'contracts': ['contrat', 'marché', 'marche', 'lot', 'prestation', 'projet'],
        'capabilities': ['capacité', 'capacite', 'compétence', 'competence', 'savoir', 'expertise', 'ressource', 'moyen']
    }
    
    # Check each column against patterns
    for col in df.columns:
        col_lower = str(col).lower()
        
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern in col_lower:
                    column_mapping[key].append(col)
                    break
    
    return column_mapping

def extract_company_name(row, column_mapping, all_columns):
    """Extract company name with enhanced detection"""
    # First try mapped columns
    for col in column_mapping.get('company_name', []):
        if pd.notna(row[col]):
            name = str(row[col]).strip()
            if name and not is_generic_value(name):
                return name
    
    # Backup: try first column with content that looks like a name
    for col in all_columns:
        if pd.notna(row[col]):
            value = str(row[col]).strip()
            if looks_like_company_name(value):
                return value
    
    return None

def looks_like_company_name(value):
    """Check if a value looks like a company name"""
    if not value or len(value) < 3 or len(value) > 100:
        return False
    
    # Check for common company words
    company_indicators = ['sa', 'sarl', 'sas', 'eurl', 'sàrl', 'eurl', 'sci', 'scp', 'snc', 'sca', 'scop', 'gmbh', 'ltd', 'inc', 'llc']
    value_lower = value.lower()
    
    # Check format and common indicators
    has_capitals = any(c.isupper() for c in value)
    has_company_indicator = any(f" {ind}" in f" {value_lower} " or f"-{ind}" in value_lower for ind in company_indicators)
    
    # If it's long enough and has proper capitalization or company indicators
    return len(value) > 4 and (has_capitals or has_company_indicator)

def is_generic_value(value):
    """Check if a value is generic and not a real name"""
    generic_values = ['oui', 'non', 'yes', 'no', 'n/a', 'na', 'nom', 'name', 'entreprise', 'company', 'valeur', 'value']
    return value.lower() in generic_values

def extract_domain(row, column_mapping, all_columns):
    """Extract company domain with domain inference"""
    # First try mapped columns
    for col in column_mapping.get('domain', []):
        if pd.notna(row[col]):
            domain = str(row[col]).strip()
            if domain and not is_generic_value(domain):
                return standardize_domain(domain)
    
    # Try to infer from company name and other fields
    company_name = extract_company_name(row, column_mapping, all_columns)
    if company_name:
        inferred_domain = infer_domain_from_name(company_name)
        if inferred_domain != "Autre":
            return inferred_domain
    
    # Try to infer from experience or contracts
    experience = extract_experience(row, column_mapping, all_columns)
    if experience and experience != "Non spécifié":
        inferred_domain = infer_domain_from_text(experience)
        if inferred_domain != "Autre":
            return inferred_domain
    
    contracts = extract_contracts(row, column_mapping, all_columns)
    if contracts:
        all_contract_text = " ".join([c.get('description', '') for c in contracts])
        inferred_domain = infer_domain_from_text(all_contract_text)
        if inferred_domain != "Autre":
            return inferred_domain
    
    return "Autre"

def standardize_domain(domain):
    """Standardize domain names"""
    domain_lower = domain.lower()
    
    domain_mapping = {
        'électricité': ['electr', 'élec', 'électr', 'energie', 'énergie', 'courant', 'tension', 'installation'],
        'mécanique': ['mécan', 'mecan', 'mécanique', 'mecanique', 'usinage', 'machine', 'moteur', 'pompe', 'turbine'],
        'hydraulique': ['hydraul', 'hydro', 'eau', 'fluide', 'tuyau', 'pompage', 'écoulement', 'échangeur', 'echangeur'],
        'bâtiment': ['bâti', 'bati', 'construct', 'btp', 'génie civil', 'genie civil', 'maçon', 'macon'],
        'maintenance': ['mainten', 'entretien', 'réparation', 'reparation', 'service', 'interventi', 'inspection']
    }
    
    for std_domain, keywords in domain_mapping.items():
        if any(keyword in domain_lower for keyword in keywords):
            return std_domain.capitalize()
    
    return domain.capitalize()

def infer_domain_from_name(name):
    """Infer domain from company name"""
    name_lower = name.lower()
    
    domain_keywords = {
        'Électricité': ['electr', 'élec', 'energ', 'énerg', 'power', 'tension', 'courant', 'eclairage', 'éclairage'],
        'Mécanique': ['mecan', 'mécan', 'usinage', 'machine', 'moteur', 'turbine', 'pompe', 'mecanique', 'mécanique'],
        'Hydraulique': ['hydraul', 'hydro', 'eau', 'fluid', 'tuyau', 'échangeur', 'echangeur', 'pompage'],
        'Bâtiment': ['batiment', 'bâtiment', 'construction', 'btp', 'genie', 'génie', 'maçon', 'macon', 'renov'],
        'Maintenance': ['mainten', 'entretien', 'service', 'répar', 'repar', 'interven', 'assist']
    }
    
    for domain, keywords in domain_keywords.items():
        if any(keyword in name_lower for keyword in keywords):
            return domain
    
    return "Autre"

def infer_domain_from_text(text):
    """Infer domain from descriptive text"""
    if not text:
        return "Autre"
    
    text_lower = text.lower()
    
    # Scores for each domain
    domain_scores = {
        'Électricité': 0,
        'Mécanique': 0,
        'Hydraulique': 0,
        'Bâtiment': 0,
        'Maintenance': 0
    }
    
    # Weighted keywords
    domain_keywords = {
        'Électricité': {
            'electricité': 5, 'électricité': 5, 'électrique': 4, 'electrique': 4, 
            'courant': 3, 'tension': 3, 'énergie': 3, 'energie': 3, 
            'tableau électrique': 4, 'installation électrique': 5
        },
        'Mécanique': {
            'mécanique': 5, 'mecanique': 5, 'usinage': 4, 'tournage': 3, 
            'fraisage': 3, 'machine': 2, 'moteur': 3, 'pompe': 2,
            'turbine': 4, 'roulement': 3, 'pièce': 2, 'piece': 2
        },
        'Hydraulique': {
            'hydraulique': 5, 'eau': 2, 'fluide': 3, 'tuyauterie': 4,
            'échangeur': 5, 'echangeur': 5, 'pompage': 4, 'vanne': 3,
            'circuit hydraulique': 5, 'pression': 2, 'débit': 2, 'debit': 2
        },
        'Bâtiment': {
            'bâtiment': 5, 'batiment': 5, 'construction': 4, 'btp': 4,
            'génie civil': 5, 'genie civil': 5, 'maçonnerie': 4, 'maconnerie': 4,
            'rénovation': 3, 'renovation': 3, 'isolation': 3
        },
        'Maintenance': {
            'maintenance': 5, 'entretien': 4, 'réparation': 4, 'reparation': 4,
            'service': 3, 'intervention': 3, 'dépannage': 4, 'depannage': 4,
            'contrôle': 3, 'controle': 3, 'inspection': 4
        }
    }
    
    # Calculate scores based on keyword occurrences
    for domain, keywords in domain_keywords.items():
        for keyword, weight in keywords.items():
            if keyword in text_lower:
                domain_scores[domain] += weight
    
    # Find the domain with the highest score
    best_domain = max(domain_scores.items(), key=lambda x: x[1])
    
    if best_domain[1] > 0:
        return best_domain[0]
    
    return "Autre"

def extract_location(row, column_mapping, all_columns):
    """Extract location with better formatting"""
    # Try mapped columns
    for col in column_mapping.get('location', []):
        if pd.notna(row[col]):
            location = str(row[col]).strip()
            if location and not is_generic_value(location):
                return format_location(location)
    
    return "Non spécifié"

def format_location(location):
    """Format location consistently"""
    # Try to extract postal code
    postal_code_match = re.search(r'\b\d{5}\b', location)
    postal_code = postal_code_match.group(0) if postal_code_match else None
    
    # Common department names and numbers
    departments = {
        '01': 'Ain', '02': 'Aisne', '03': 'Allier', '04': 'Alpes-de-Haute-Provence',
        '05': 'Hautes-Alpes', '06': 'Alpes-Maritimes', '07': 'Ardèche', '08': 'Ardennes',
        '09': 'Ariège', '10': 'Aube', '11': 'Aude', '12': 'Aveyron', '13': 'Bouches-du-Rhône',
        '14': 'Calvados', '15': 'Cantal', '16': 'Charente', '17': 'Charente-Maritime',
        '18': 'Cher', '19': 'Corrèze', '21': 'Côte-d\'Or', '22': 'Côtes-d\'Armor',
        '23': 'Creuse', '24': 'Dordogne', '25': 'Doubs', '26': 'Drôme', '27': 'Eure',
        '28': 'Eure-et-Loir', '29': 'Finistère', '2A': 'Corse-du-Sud', '2B': 'Haute-Corse',
        '30': 'Gard', '31': 'Haute-Garonne', '32': 'Gers', '33': 'Gironde', '34': 'Hérault',
        '35': 'Ille-et-Vilaine', '36': 'Indre', '37': 'Indre-et-Loire', '38': 'Isère',
        '39': 'Jura', '40': 'Landes', '41': 'Loir-et-Cher', '42': 'Loire', '43': 'Haute-Loire',
        '44': 'Loire-Atlantique', '45': 'Loiret', '46': 'Lot', '47': 'Lot-et-Garonne',
        '48': 'Lozère', '49': 'Maine-et-Loire', '50': 'Manche', '51': 'Marne',
        '52': 'Haute-Marne', '53': 'Mayenne', '54': 'Meurthe-et-Moselle', '55': 'Meuse',
        '56': 'Morbihan', '57': 'Moselle', '58': 'Nièvre', '59': 'Nord', '60': 'Oise',
        '61': 'Orne', '62': 'Pas-de-Calais', '63': 'Puy-de-Dôme', '64': 'Pyrénées-Atlantiques',
        '65': 'Hautes-Pyrénées', '66': 'Pyrénées-Orientales', '67': 'Bas-Rhin',
        '68': 'Haut-Rhin', '69': 'Rhône', '70': 'Haute-Saône', '71': 'Saône-et-Loire',
        '72': 'Sarthe', '73': 'Savoie', '74': 'Haute-Savoie', '75': 'Paris',
        '76': 'Seine-Maritime', '77': 'Seine-et-Marne', '78': 'Yvelines', '79': 'Deux-Sèvres',
        '80': 'Somme', '81': 'Tarn', '82': 'Tarn-et-Garonne', '83': 'Var', '84': 'Vaucluse',
        '85': 'Vendée', '86': 'Vienne', '87': 'Haute-Vienne', '88': 'Vosges', '89': 'Yonne',
        '90': 'Territoire de Belfort', '91': 'Essonne', '92': 'Hauts-de-Seine',
        '93': 'Seine-Saint-Denis', '94': 'Val-de-Marne', '95': 'Val-d\'Oise'
    }
    
    # Extract department code
    dept_code = None
    if postal_code:
        dept_code = postal_code[:2]
        dept_name = departments.get(dept_code, '')
        
        # Format as "City, Department (code)"
        city_match = re.sub(r'\b\d{5}\b', '', location).strip().strip(',.-')
        if city_match:
            return f"{city_match}, {dept_name} ({dept_code})"
        else:
            return f"{dept_name} ({dept_code})"
    
    # If no postal code, return as is
    return location

def extract_certifications(row, column_mapping, all_columns):
    """Extract certifications with better detection"""
    certifications = []
    
    # Common certification patterns
    cert_patterns = {
        'MASE': ['mase'],
        'ISO 9001': ['iso 9001', 'iso9001', 'qualité', 'qualite'],
        'ISO 14001': ['iso 14001', 'iso14001', 'environnement'],
        'ISO 45001': ['iso 45001', 'iso45001', 'sécurité', 'securite'],
        'QUALIBAT': ['qualibat'],
        'QUALIFELEC': ['qualifelec'],
        'CEFRI': ['cefri'],
        'RGE': ['rge'],
        'ECOVADIS': ['ecovadis']
    }
    
    # Check mapped columns
    for col in column_mapping.get('certifications', []):
        if pd.notna(row[col]):
            cert_text = str(row[col]).lower()
            for cert_name, patterns in cert_patterns.items():
                if any(pattern in cert_text for pattern in patterns):
                    if cert_name not in certifications:
                        certifications.append(cert_name)
    
    # Check all other columns for certification mentions
    if not certifications:
        for col in all_columns:
            if pd.notna(row[col]):
                cert_text = str(row[col]).lower()
                for cert_name, patterns in cert_patterns.items():
                    if any(pattern in cert_text for pattern in patterns):
                        if cert_name not in certifications:
                            certifications.append(cert_name)
    
    return certifications

def extract_ca(row, column_mapping, all_columns):
    """Extract CA (chiffre d'affaires) with better formatting"""
    # Try mapped columns
    for col in column_mapping.get('ca', []):
        if pd.notna(row[col]):
            ca_value = row[col]
            if isinstance(ca_value, (int, float)) and ca_value > 0:
                return format_ca(ca_value)
            elif isinstance(ca_value, str) and ca_value.strip():
                ca_clean = ca_value.strip()
                # Try to extract numbers
                numbers = re.findall(r'[\d.,]+', ca_clean.replace(' ', ''))
                if numbers:
                    try:
                        # Replace comma with dot and convert to float
                        amount = float(numbers[0].replace(',', '.'))
                        return format_ca(amount)
                    except ValueError:
                        pass
                return ca_clean
    
    # Check all other columns for CA mentions
    for col in all_columns:
        if pd.notna(row[col]) and any(term in str(col).lower() for term in ['ca', 'chiffre']):
            ca_value = row[col]
            if isinstance(ca_value, (int, float)) and ca_value > 0:
                return format_ca(ca_value)
            elif isinstance(ca_value, str) and ca_value.strip():
                ca_clean = ca_value.strip()
                numbers = re.findall(r'[\d.,]+', ca_clean.replace(' ', ''))
                if numbers:
                    try:
                        amount = float(numbers[0].replace(',', '.'))
                        return format_ca(amount)
                    except ValueError:
                        pass
    
    return "Non spécifié"

def format_ca(amount):
    """Format CA value consistently"""
    if amount >= 1000000:
        return f"{amount/1000000:.1f}M€"
    elif amount >= 1000:
        return f"{amount/1000:.0f}k€"
    else:
        return f"{amount:.0f}€"

def extract_employees(row, column_mapping, all_columns):
    """Extract employee count with better detection"""
    # Try mapped columns
    for col in column_mapping.get('employees', []):
        if pd.notna(row[col]):
            emp_value = row[col]
            if isinstance(emp_value, (int, float)) and emp_value > 0:
                return str(int(emp_value))
            elif isinstance(emp_value, str) and emp_value.strip():
                emp_clean = emp_value.strip()
                numbers = re.findall(r'\d+', emp_clean)
                if numbers:
                    return numbers[0]
                return emp_clean
    
    # Check all other columns for employee mentions
    for col in all_columns:
        if pd.notna(row[col]) and any(term in str(col).lower() for term in ['effectif', 'salarié', 'employé']):
            emp_value = row[col]
            if isinstance(emp_value, (int, float)) and emp_value > 0:
                return str(int(emp_value))
            elif isinstance(emp_value, str) and emp_value.strip():
                emp_clean = emp_value.strip()
                numbers = re.findall(r'\d+', emp_clean)
                if numbers:
                    return numbers[0]
    
    return "Non spécifié"

def extract_contact_info(row, column_mapping, all_columns):
    """Extract contact information with better formatting"""
    contact = {}
    
    # Extract email
    for col in column_mapping.get('email', []):
        if pd.notna(row[col]):
            email = str(row[col]).strip()
            if '@' in email and '.' in email:
                contact['email'] = email
                break
    
    # Extract phone
    for col in column_mapping.get('phone', []):
        if pd.notna(row[col]):
            phone = str(row[col]).strip()
            if re.search(r'[\d\s\.]{8,}', phone):
                contact['phone'] = format_phone_number(phone)
                break
    
    # Check all other columns for contact info
    if 'email' not in contact:
        for col in all_columns:
            if pd.notna(row[col]):
                value = str(row[col])
                if '@' in value and '.' in value and re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', value):
                    contact['email'] = value.strip()
                    break
    
    if 'phone' not in contact and contact:  # Only look for phone if we already have email
        for col in all_columns:
            if pd.notna(row[col]):
                value = str(row[col])
                if re.search(r'(0|\+33)\s*[1-9](\s*\d{2}){4}', value):
                    contact['phone'] = format_phone_number(value)
                    break
    
    return contact if contact else None

def format_phone_number(phone):
    """Format phone number consistently"""
    # Remove all non-digits
    digits = re.sub(r'\D', '', phone)
    
    # Check if it's a French number
    if len(digits) == 10 and digits.startswith('0'):
        # Format as 01 23 45 67 89
        return ' '.join([digits[i:i+2] for i in range(0, 10, 2)])
    elif len(digits) > 10 and (digits.startswith('33') or digits.startswith('0033')):
        # International format, remove country code and add 0
        if digits.startswith('0033'):
            digits = '0' + digits[4:]
        else:
            digits = '0' + digits[2:]
        return ' '.join([digits[i:i+2] for i in range(0, 10, 2)])
    
    # Return as is if we can't format it
    return phone

def extract_experience(row, column_mapping, all_columns):
    """Extract experience with better formatting"""
    # Try mapped columns
    for col in column_mapping.get('experience', []):
        if pd.notna(row[col]):
            exp = str(row[col]).strip()
            if exp and len(exp) > 10:  # Ensure it's substantial
                return exp
    
    # Check all other columns for experience mentions
    for col in all_columns:
        if pd.notna(row[col]) and any(term in str(col).lower() for term in ['expérience', 'référence', 'historique']):
            exp = str(row[col]).strip()
            if exp and len(exp) > 10:
                return exp
    
    return "Non spécifié"

def extract_contracts(row, column_mapping, all_columns):
    """Extract contracts and projects information"""
    contracts = []
    
    # Try mapped columns
    for col in column_mapping.get('contracts', []):
        if pd.notna(row[col]):
            contract_text = str(row[col]).strip()
            if contract_text and len(contract_text) > 5:
                contracts.append({
                    'type': 'Contrat',
                    'description': contract_text
                })
    
    # Check all other columns for contract mentions
    if not contracts:
        contract_keywords = ['contrat', 'marché', 'marche', 'lot', 'prestation', 'projet', 'affaire', 'commande']
        for col in all_columns:
            if pd.notna(row[col]) and any(keyword in str(col).lower() for keyword in contract_keywords):
                contract_text = str(row[col]).strip()
                if contract_text and len(contract_text) > 5:
                    contracts.append({
                        'type': str(col),
                        'description': contract_text
                    })
    
    return contracts

def extract_capabilities(row, column_mapping, all_columns):
    """Extract technical capabilities"""
    capabilities = []
    
    # Try mapped columns
    for col in column_mapping.get('capabilities', []):
        if pd.notna(row[col]):
            cap_text = str(row[col]).strip()
            if cap_text and len(cap_text) > 5:
                capabilities.append(cap_text)
    
    # Check all other columns for capability mentions
    capability_keywords = ['capacité', 'capacite', 'compétence', 'competence', 'savoir', 'expertise', 'moyen']
    for col in all_columns:
        if pd.notna(row[col]) and any(keyword in str(col).lower() for keyword in capability_keywords):
            cap_text = str(row[col]).strip()
            if cap_text and len(cap_text) > 5 and cap_text not in capabilities:
                capabilities.append(cap_text)
    
    return capabilities

def enrich_company_data(companies):
    """Add inferred data to companies to improve matching"""
    for company in companies:
        # Enrich domain information if needed
        if company['domain'] == "Autre" and company['name']:
            # Try to infer from name
            inferred_domain = infer_domain_from_name(company['name'])
            if inferred_domain != "Autre":
                company['domain'] = inferred_domain
                logger.info(f"Inferred domain '{inferred_domain}' for {company['name']}")
            
            # Try to infer from experience or contracts
            if company['domain'] == "Autre" and company['experience'] != "Non spécifié":
                inferred_domain = infer_domain_from_text(company['experience'])
                if inferred_domain != "Autre":
                    company['domain'] = inferred_domain
                    logger.info(f"Inferred domain '{inferred_domain}' from experience for {company['name']}")
            
            if company['domain'] == "Autre" and company['lots_marches']:
                all_contract_text = " ".join([c.get('description', '') for c in company['lots_marches']])
                inferred_domain = infer_domain_from_text(all_contract_text)
                if inferred_domain != "Autre":
                    company['domain'] = inferred_domain
                    logger.info(f"Inferred domain '{inferred_domain}' from contracts for {company['name']}")
        
        # Add keywords for better matching
        company['keywords'] = generate_company_keywords(company)
        
        # Add geographic information
        company['geo_zone'] = determine_geo_zone(company['location'])

def generate_company_keywords(company):
    """Generate keywords for better company matching"""
    keywords = []
    
    # Add domain keywords
    if company['domain'] != "Autre":
        keywords.append(company['domain'].lower())
        
        # Add domain-specific keywords
        domain_specific = {
            'Électricité': ['électrique', 'électricien', 'courant', 'installation'],
            'Mécanique': ['mécanique', 'usinage', 'pièces', 'machines'],
            'Hydraulique': ['hydraulique', 'fluide', 'eau', 'échangeur'],
            'Bâtiment': ['construction', 'bâtiment', 'génie civil', 'chantier'],
            'Maintenance': ['maintenance', 'entretien', 'réparation', 'service']
        }
        
        if company['domain'] in domain_specific:
            keywords.extend(domain_specific[company['domain']])
    
    # Add certification keywords
    for cert in company['certifications']:
        keywords.append(cert.lower())
        if cert == 'MASE':
            keywords.append('sécurité')
            keywords.append('hse')
        elif 'ISO' in cert:
            keywords.append('qualité')
            keywords.append('certification')
    
    # Add size keywords
    if company['employees'] != "Non spécifié":
        try:
            emp_count = int(re.findall(r'\d+', company['employees'])[0])
            if emp_count > 100:
                keywords.append('grande entreprise')
            elif emp_count > 50:
                keywords.append('entreprise moyenne')
            elif emp_count > 10:
                keywords.append('petite entreprise')
            else:
                keywords.append('très petite entreprise')
        except:
            pass
    
    # Add location keywords
    if company['geo_zone'] != "Non spécifié":
        keywords.append(company['geo_zone'].lower())
    
    # Add keywords from capabilities
    if company['capabilities']:
        for cap in company['capabilities']:
            cap_words = cap.lower().split()
            for word in cap_words:
                if len(word) > 4 and word not in keywords:
                    keywords.append(word)
    
    return list(set(keywords))  # Remove duplicates

def determine_geo_zone(location):
    """Determine geographic zone from location"""
    if location == "Non spécifié":
        return "Non spécifié"
    
    location_lower = location.lower()
    
    # Regions
    regions = {
        'Ile-de-France': ['paris', 'ile-de-france', 'idf', '75', '77', '78', '91', '92', '93', '94', '95'],
        'Nord': ['nord', 'hauts-de-france', 'lille', 'amiens', '59', '62', '80', '60', '02'],
        'Est': ['est', 'grand est', 'alsace', 'lorraine', 'champagne', 'strasbourg', 'nancy', 'metz', 'reims', 'mulhouse', '67', '68', '57', '54', '55', '88', '08', '51', '52', '10'],
        'Ouest': ['ouest', 'bretagne', 'normandie', 'pays de la loire', 'rennes', 'nantes', 'caen', 'rouen', 'angers', '35', '44', '29', '56', '22', '50', '14', '61', '53', '72', '49', '85'],
        'Sud-Ouest': ['sud-ouest', 'nouvelle-aquitaine', 'bordeaux', 'toulouse', 'pau', 'bayonne', '33', '40', '64', '65', '32', '31', '09', '81', '82'],
        'Sud-Est': ['sud-est', 'paca', 'rhone-alpes', 'auvergne', 'marseille', 'lyon', 'nice', 'grenoble', '13', '84', '04', '05', '06', '83', '69', '38', '73', '74', '01', '26', '07'],
        'Centre': ['centre', 'centre-val de loire', 'orleans', 'tours', 'bourges', '45', '41', '37', '36', '18', '28'],
        'Ardennes': ['ardennes', 'charleville', 'sedan', 'chooz', '08']  # Special for Chooz project
    }
    
    for region, keywords in regions.items():
        if any(keyword in location_lower for keyword in keywords):
            return region
    
    # Try to extract department from postal code
    postal_match = re.search(r'\b(\d{2})\d{3}\b', location_lower)
    if postal_match:
        dept = postal_match.group(1)
        
        # Map department to region
        dept_regions = {
            # Ile-de-France
            '75': 'Ile-de-France', '77': 'Ile-de-France', '78': 'Ile-de-France', 
            '91': 'Ile-de-France', '92': 'Ile-de-France', '93': 'Ile-de-France', 
            '94': 'Ile-de-France', '95': 'Ile-de-France',
            # Nord
            '59': 'Nord', '62': 'Nord', '80': 'Nord', '60': 'Nord', '02': 'Nord',
            # Est
            '67': 'Est', '68': 'Est', '57': 'Est', '54': 'Est', '55': 'Est', 
            '88': 'Est', '08': 'Est', '51': 'Est', '52': 'Est', '10': 'Est',
            # Ardennes (special case for Chooz)
            '08': 'Ardennes',
            # Rest of France by region...
        }
        
        if dept in dept_regions:
            return dept_regions[dept]
    
    # If nothing matches
    return "France"  # Default to national