import pandas as pd
import os
import re
import numpy as np
from datetime import datetime

def load_companies_from_excel(file_path):
    """
    Charge les entreprises depuis le fichier Excel avec extraction améliorée des domaines
    """
    try:
        print(f"=== CHARGEMENT EXCEL ===")
        print(f"Fichier: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"ERREUR: Fichier non trouvé - {file_path}")
            return []
            
        # Charger le fichier Excel
        xl_file = pd.ExcelFile(file_path, engine='openpyxl')
        print(f"Feuilles disponibles: {xl_file.sheet_names}")
        
        # Utiliser la première feuille ou chercher une feuille avec des données
        main_sheet = xl_file.sheet_names[0]
        df = pd.read_excel(file_path, sheet_name=main_sheet, engine='openpyxl')
        
        print(f"Dimensions du DataFrame: {df.shape}")
        print(f"Colonnes: {list(df.columns)}")
        
        # Nettoyer les colonnes
        df.columns = df.columns.astype(str).str.strip()
        
        companies = []
        
        for idx, row in df.iterrows():
            try:
                # Ignorer les lignes complètement vides
                if row.isna().all():
                    continue
                
                # Extraire les informations de base
                company_name = extract_company_name(row, df.columns)
                if not company_name or company_name.strip() == "":
                    continue
                
                # Créer un ID unique
                company_id = f"ENT_{str(len(companies) + 1).zfill(3)}"
                
                # Extraire toutes les informations
                location = extract_location(row, df.columns)
                certifications = extract_certifications(row, df.columns)
                ca = extract_ca(row, df.columns)
                employees = extract_employees(row, df.columns)
                contact_info = extract_contact_info(row, df.columns)
                experience = extract_experience(row, df.columns)
                
                # NOUVEAU: Extraire les lots/marchés pour déterminer le domaine d'activité
                lots_info = extract_lots_marches(row, df.columns)
                domain = determine_domain_from_data(company_name, lots_info, row, df.columns)
                
                # Créer l'objet entreprise avec le nouveau format
                company = {
                    'id': company_id,
                    'name': company_name,
                    'location': location if location else 'Non spécifié',
                    'domain': domain,
                    'certifications': certifications,
                    'ca': ca if ca else 'Non spécifié',
                    'employees': employees if employees else 'Non spécifié',
                    'contact': contact_info,
                    'experience': experience if experience else 'Non spécifié',
                    'lots_marches': lots_info,  # NOUVEAU: Historique des lots
                    'score': 0
                }
                
                companies.append(company)
                
            except Exception as e:
                print(f"Erreur ligne {idx}: {e}")
                continue
        
        print(f"=== RÉSULTAT EXTRACTION ===")
        print(f"Entreprises extraites: {len(companies)}")
        
        # Afficher des statistiques sur les domaines
        domain_stats = {}
        for company in companies:
            domain = company['domain']
            domain_stats[domain] = domain_stats.get(domain, 0) + 1
        
        print("Répartition par domaine:")
        for domain, count in domain_stats.items():
            print(f"  {domain}: {count}")
        
        return companies
        
    except Exception as e:
        print(f"ERREUR lors du chargement: {e}")
        import traceback
        print(traceback.format_exc())
        return []

def extract_company_name(row, columns):
    """Extrait le nom de l'entreprise avec plus de patterns"""
    patterns = [
        'RAISON SOCIALE', 'Raison sociale', 'raison sociale',
        'NOM ENTREPRISE', 'Nom entreprise', 'nom entreprise',
        'ENTREPRISE', 'Entreprise', 'entreprise',
        'SOCIETE', 'Société', 'société',
        'DENOMINATION', 'Dénomination', 'dénomination',
        'NOM', 'Nom', 'nom',
        'LIBELLE', 'Libellé', 'libellé',
        'DESIGNATION', 'Désignation', 'désignation',
        'TITULAIRE', 'Titulaire', 'titulaire'
    ]
    
    for pattern in patterns:
        for col in columns:
            if pattern in str(col) and pd.notna(row[col]):
                name = str(row[col]).strip()
                if name and name.lower() not in ['nan', 'none', 'null', '']:
                    return name
    
    # Si aucun nom explicite, prendre la première colonne non-vide
    for col in columns:
        if pd.notna(row[col]):
            value = str(row[col]).strip()
            if len(value) > 3 and len(value) < 100:  # Nom raisonnable
                return value
    
    return None

def extract_lots_marches(row, columns):
    """NOUVEAU: Extrait les informations sur les lots et marchés"""
    lots_info = []
    
    # Chercher des colonnes contenant des infos sur les lots/marchés
    lot_patterns = [
        'LOT', 'Lot', 'lot',
        'MARCHE', 'Marché', 'marché', 'marche',
        'CONTRAT', 'Contrat', 'contrat',
        'PRESTATION', 'Prestation', 'prestation',
        'TRAVAUX', 'Travaux', 'travaux',
        'SERVICE', 'Service', 'service',
        'OBJET', 'Objet', 'objet',
        'DESCRIPTION', 'Description', 'description',
        'ACTIVITE', 'Activité', 'activité', 'activite'
    ]
    
    for col in columns:
        col_lower = str(col).lower()
        for pattern in lot_patterns:
            if pattern.lower() in col_lower and pd.notna(row[col]):
                value = str(row[col]).strip()
                if value and len(value) > 5:  # Éviter les valeurs trop courtes
                    lots_info.append({
                        'type': col,
                        'description': value
                    })
    
    return lots_info

def determine_domain_from_data(company_name, lots_info, row, columns):
    """NOUVEAU: Détermine le domaine d'activité basé sur toutes les données disponibles"""
    
    # Analyser le nom de l'entreprise
    name_domain = analyze_company_name_for_domain(company_name)
    if name_domain != 'Autre':
        return name_domain
    
    # Analyser les lots/marchés
    if lots_info:
        lots_domain = analyze_lots_for_domain(lots_info)
        if lots_domain != 'Autre':
            return lots_domain
    
    # Analyser toutes les colonnes pour trouver des indices
    all_text = ""
    for col in columns:
        if pd.notna(row[col]):
            all_text += " " + str(row[col]).lower()
    
    return analyze_text_for_domain(all_text)

def analyze_company_name_for_domain(name):
    """Analyse le nom de l'entreprise pour déterminer le domaine"""
    if not name:
        return 'Autre'
    
    name_lower = name.lower()
    
    # Mots-clés par domaine
    domain_keywords = {
        'Électricité': [
            'electr', 'élec', 'energie', 'énergie', 'power', 'volt', 'amp',
            'electricite', 'électricité', 'energetique', 'énergétique',
            'courant', 'tension', 'installation', 'câblage', 'eclairage'
        ],
        'Mécanique': [
            'mecani', 'mécan', 'mechanic', 'usinage', 'tournage', 'fraisage',
            'machine', 'moteur', 'pompe', 'turbine', 'compresseur',
            'maintenance', 'reparation', 'réparation', 'pieces', 'pièces'
        ],
        'Hydraulique': [
            'hydraul', 'eau', 'water', 'fluide', 'pipeline', 'tuyauterie',
            'plomberie', 'canalisation', 'robinet', 'vanne', 'circuit',
            'pression', 'debit', 'débit', 'aqua'
        ],
        'Bâtiment': [
            'batiment', 'bâtiment', 'construction', 'btp', 'genie civil',
            'génie civil', 'maconnerie', 'maçonnerie', 'charpente',
            'couverture', 'isolation', 'renovation', 'rénovation',
            'travaux publics', 'terrassement'
        ],
        'Maintenance': [
            'maintenance', 'entretien', 'service', 'reparation', 'réparation',
            'depot', 'dépôt', 'intervention', 'assistance', 'support',
            'controle', 'contrôle', 'inspection', 'verification', 'vérification'
        ]
    }
    
    # Vérifier chaque domaine
    for domain, keywords in domain_keywords.items():
        for keyword in keywords:
            if keyword in name_lower:
                return domain
    
    return 'Autre'

def analyze_lots_for_domain(lots_info):
    """Analyse les lots pour déterminer le domaine d'activité"""
    if not lots_info:
        return 'Autre'
    
    # Concaténer toutes les descriptions de lots
    all_lots_text = ""
    for lot in lots_info:
        all_lots_text += " " + lot.get('description', '').lower()
    
    return analyze_text_for_domain(all_lots_text)

def analyze_text_for_domain(text):
    """Analyse un texte pour déterminer le domaine d'activité"""
    if not text:
        return 'Autre'
    
    text_lower = text.lower()
    
    # Scores par domaine
    domain_scores = {
        'Électricité': 0,
        'Mécanique': 0,
        'Hydraulique': 0,
        'Bâtiment': 0,
        'Maintenance': 0
    }
    
    # Mots-clés pondérés
    domain_keywords = {
        'Électricité': {
            'electr': 5, 'élec': 5, 'energie': 3, 'énergie': 3,
            'installation electrique': 5, 'installation électrique': 5,
            'courant': 2, 'tension': 2, 'eclairage': 3, 'éclairage': 3,
            'tableau': 2, 'disjoncteur': 3, 'transformateur': 4,
            'alternateur': 4, 'generateur': 3, 'générateur': 3
        },
        'Mécanique': {
            'mecani': 5, 'mécan': 5, 'usinage': 4, 'tournage': 3,
            'fraisage': 3, 'machine': 2, 'moteur': 3, 'pompe': 2,
            'turbine': 4, 'compresseur': 3, 'pieces': 2, 'pièces': 2,
            'roulement': 3, 'palier': 3, 'engrenage': 3
        },
        'Hydraulique': {
            'hydraul': 5, 'eau': 2, 'fluide': 3, 'tuyauterie': 4,
            'canalisation': 3, 'robinet': 2, 'vanne': 3,
            'circuit hydraulique': 5, 'pression': 2, 'debit': 2,
            'échangeur': 4, 'chaudiere': 3, 'chaudière': 3
        },
        'Bâtiment': {
            'batiment': 5, 'bâtiment': 5, 'construction': 3,
            'btp': 4, 'genie civil': 4, 'génie civil': 4,
            'maconnerie': 3, 'maçonnerie': 3, 'charpente': 3,
            'isolation': 2, 'renovation': 2, 'rénovation': 2
        },
        'Maintenance': {
            'maintenance': 5, 'entretien': 4, 'reparation': 3,
            'réparation': 3, 'intervention': 2, 'controle': 2,
            'contrôle': 2, 'inspection': 3, 'verification': 2,
            'vérification': 2, 'preventif': 3, 'préventif': 3
        }
    }
    
    # Calculer les scores
    for domain, keywords in domain_keywords.items():
        for keyword, weight in keywords.items():
            if keyword in text_lower:
                domain_scores[domain] += weight
    
    # Trouver le domaine avec le meilleur score
    best_domain = max(domain_scores.items(), key=lambda x: x[1])
    
    if best_domain[1] > 0:
        return best_domain[0]
    
    return 'Autre'

def extract_location(row, columns):
    """Extrait la localisation avec patterns étendus"""
    patterns = [
        'VILLE', 'Ville', 'ville',
        'LOCALISATION', 'Localisation', 'localisation',
        'ADRESSE', 'Adresse', 'adresse',
        'COMMUNE', 'Commune', 'commune',
        'LIEU', 'Lieu', 'lieu',
        'DEPARTEMENT', 'Département', 'département',
        'REGION', 'Région', 'région',
        'CODE POSTAL', 'Code postal', 'code postal',
        'CP', 'Cp', 'cp'
    ]
    
    for pattern in patterns:
        for col in columns:
            if pattern in str(col) and pd.notna(row[col]):
                location = str(row[col]).strip()
                if location and location.lower() not in ['nan', 'none', 'null']:
                    return location
    return None

def extract_certifications(row, columns):
    """Extrait les certifications avec détection améliorée"""
    certifications = []
    
    # Patterns de certifications
    cert_patterns = {
        'MASE': ['mase'],
        'ISO 9001': ['iso 9001', 'iso9001', 'qualité'],
        'ISO 14001': ['iso 14001', 'iso14001', 'environnement'],
        'QUALIBAT': ['qualibat'],
        'QUALIBOIS': ['qualibois'],
        'RGE': ['rge'],
        'CEFRI': ['cefri']
    }
    
    # Chercher dans toutes les colonnes
    for col in columns:
        if pd.notna(row[col]):
            value = str(row[col]).lower()
            
            for cert_name, patterns in cert_patterns.items():
                for pattern in patterns:
                    if pattern in value:
                        if cert_name not in certifications:
                            certifications.append(cert_name)
    
    return certifications

def extract_ca(row, columns):
    """Extrait le chiffre d'affaires"""
    patterns = [
        'CA', 'C.A.', 'C.A', 'ca',
        'CHIFFRE AFFAIRES', 'Chiffre affaires', 'chiffre affaires',
        'CHIFFRE D\'AFFAIRES', 'Chiffre d\'affaires',
        'CA ANNUEL', 'Ca annuel', 'ca annuel',
        'TURNOVER', 'Turnover', 'turnover'
    ]
    
    for pattern in patterns:
        for col in columns:
            if pattern in str(col) and pd.notna(row[col]):
                ca_value = row[col]
                
                if isinstance(ca_value, (int, float)):
                    if ca_value > 0:
                        return format_ca(ca_value)
                elif isinstance(ca_value, str):
                    ca_clean = ca_value.strip()
                    if ca_clean:
                        # Essayer d'extraire un nombre
                        numbers = re.findall(r'[\d,\.]+', ca_clean)
                        if numbers:
                            try:
                                amount = float(numbers[0].replace(',', '.'))
                                return format_ca(amount)
                            except ValueError:
                                pass
                        return ca_clean
    return None

def format_ca(amount):
    """Formate le chiffre d'affaires"""
    if amount >= 1000000:
        return f"{amount/1000000:.1f}M€"
    elif amount >= 1000:
        return f"{amount/1000:.0f}k€"
    else:
        return f"{amount:.0f}€"

def extract_employees(row, columns):
    """Extrait le nombre d'employés"""
    patterns = [
        'EFFECTIF', 'Effectif', 'effectif',
        'EFFECTIFS', 'Effectifs', 'effectifs',
        'NB SALARIES', 'Nb salariés', 'nb salariés',
        'NOMBRE EMPLOYES', 'Nombre employés',
        'PERSONNEL', 'Personnel', 'personnel',
        'SALARIES', 'Salariés', 'salariés'
    ]
    
    for pattern in patterns:
        for col in columns:
            if pattern in str(col) and pd.notna(row[col]):
                emp_value = row[col]
                
                if isinstance(emp_value, (int, float)):
                    if emp_value > 0:
                        return str(int(emp_value))
                elif isinstance(emp_value, str):
                    emp_clean = emp_value.strip()
                    if emp_clean:
                        numbers = re.findall(r'\d+', emp_clean)
                        if numbers:
                            return numbers[0]
                        return emp_clean
    return None

def extract_contact_info(row, columns):
    """Extrait les informations de contact"""
    contact = {}
    
    # Email
    email_patterns = ['EMAIL', 'Email', 'email', 'MAIL', 'Mail', 'mail']
    for pattern in email_patterns:
        for col in columns:
            if pattern in str(col) and pd.notna(row[col]):
                email = str(row[col]).strip()
                if '@' in email:
                    contact['email'] = email
                    break
    
    # Téléphone
    phone_patterns = ['TELEPHONE', 'Téléphone', 'TEL', 'Tel', 'tel', 'PHONE']
    for pattern in phone_patterns:
        for col in columns:
            if pattern in str(col) and pd.notna(row[col]):
                phone = str(row[col]).strip()
                if phone and len(phone) > 5:
                    contact['phone'] = phone
                    break
    
    return contact if contact else None

def extract_experience(row, columns):
    """Extrait l'expérience ou références"""
    patterns = [
        'EXPERIENCE', 'Expérience', 'expérience',
        'REFERENCES', 'Références', 'références',
        'PROJETS', 'Projets', 'projets',
        'REALISATIONS', 'Réalisations', 'réalisations',
        'HISTORIQUE', 'Historique', 'historique'
    ]
    
    for pattern in patterns:
        for col in columns:
            if pattern in str(col) and pd.notna(row[col]):
                exp = str(row[col]).strip()
                if exp and len(exp) > 10:  # Description substantielle
                    return exp
    return None