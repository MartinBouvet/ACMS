import pandas as pd
import os
import re
import numpy as np

def load_companies_from_excel(file_path):
    """
    Charge les entreprises depuis le fichier Excel ACMS avec extraction améliorée
    
    Args:
        file_path: Chemin vers le fichier Excel
        
    Returns:
        Liste des entreprises au format attendu par l'application
    """
    try:
        print(f"Tentative de chargement du fichier: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"Fichier non trouvé: {file_path}")
            return []
            
        # Charger le fichier Excel avec différentes feuilles possibles
        xl_file = pd.ExcelFile(file_path, engine='openpyxl')
        print(f"Feuilles disponibles: {xl_file.sheet_names}")
        
        # Essayer de trouver la feuille principale
        main_sheet = None
        for sheet_name in xl_file.sheet_names:
            if any(keyword in sheet_name.lower() for keyword in ['entreprise', 'acms', 'publi', 'societe', 'liste']):
                main_sheet = sheet_name
                break
        
        if main_sheet is None:
            main_sheet = xl_file.sheet_names[0]  # Prendre la première feuille par défaut
        
        print(f"Utilisation de la feuille: {main_sheet}")
        
        # Charger la feuille avec gestion des en-têtes
        df = pd.read_excel(file_path, sheet_name=main_sheet, engine='openpyxl')
        
        # Nettoyer les colonnes (supprimer les espaces en début/fin)
        df.columns = df.columns.astype(str).str.strip()
        
        print("Colonnes détectées dans le fichier Excel:")
        for i, col in enumerate(df.columns):
            print(f"  {i}: '{col}'")
        
        # Afficher quelques lignes d'exemple pour déboguer
        print("\nPremières lignes du fichier:")
        print(df.head(3))
        
        companies = []
        
        # Parcourir les lignes et extraire les données
        for idx, row in df.iterrows():
            try:
                # Ignorer les lignes vides
                if row.isna().all():
                    continue
                
                # Créer un identifiant unique
                company_id = f"ENT_{str(idx + 1).zfill(3)}"
                
                # Extraire le nom de l'entreprise
                company_name = extract_company_name(row, df.columns)
                if not company_name or company_name.strip() == "":
                    continue  # Ignorer les lignes sans nom d'entreprise
                
                # Extraire les autres informations
                location = extract_location(row, df.columns)
                certifications = extract_certifications(row, df.columns)
                ca = extract_ca(row, df.columns)
                employees = extract_employees(row, df.columns)
                domain = extract_domain(row, df.columns)
                contact_info = extract_contact_info(row, df.columns)
                experience = extract_experience(row, df.columns)
                
                # Créer l'objet entreprise
                company = {
                    'id': company_id,
                    'name': company_name,
                    'location': location if location else 'Non spécifié',
                    'domain': domain if domain else 'Non spécifié',
                    'certifications': certifications,
                    'ca': ca if ca else 'Non spécifié',
                    'employees': employees if employees else 'Non spécifié',
                    'contact': contact_info,
                    'experience': experience if experience else 'Non spécifié',
                    'score': 0  # Score par défaut
                }
                
                companies.append(company)
                
            except Exception as e:
                print(f"Erreur lors du traitement de la ligne {idx}: {e}")
                continue
        
        print(f"Nombre d'entreprises extraites: {len(companies)}")
        
        # Afficher quelques exemples d'entreprises extraites
        if companies:
            print("\nExemples d'entreprises extraites:")
            for i, company in enumerate(companies[:3]):
                print(f"  Entreprise {i+1}:")
                print(f"    Nom: {company['name']}")
                print(f"    Localisation: {company['location']}")
                print(f"    Domaine: {company['domain']}")
                print(f"    Certifications: {company['certifications']}")
        
        return companies
        
    except Exception as e:
        print(f"Erreur lors du chargement du fichier Excel: {e}")
        import traceback
        print(traceback.format_exc())
        return []

def extract_company_name(row, columns):
    """Extrait le nom de l'entreprise"""
    possible_columns = [
        'RAISON SOCIALE', 'Raison sociale', 'raison sociale',
        'NOM ENTREPRISE', 'Nom entreprise', 'nom entreprise',
        'ENTREPRISE', 'Entreprise', 'entreprise',
        'SOCIETE', 'Société', 'société',
        'DENOMINATION', 'Dénomination', 'dénomination',
        'NOM', 'Nom', 'nom',
        'LIBELLE', 'Libellé', 'libellé',
        'DESIGNATION', 'Désignation', 'désignation'
    ]
    
    for col in possible_columns:
        if col in columns and pd.notna(row[col]):
            name = str(row[col]).strip()
            if name and name != "" and name.lower() not in ['nan', 'none', 'null']:
                return name
    return None

def extract_location(row, columns):
    """Extrait la localisation de l'entreprise"""
    possible_columns = [
        'VILLE', 'Ville', 'ville',
        'LOCALISATION', 'Localisation', 'localisation',
        'ADRESSE', 'Adresse', 'adresse',
        'COMMUNE', 'Commune', 'commune',
        'LIEU', 'Lieu', 'lieu',
        'DEPARTEMENT', 'Département', 'département',
        'REGION', 'Région', 'région'
    ]
    
    for col in possible_columns:
        if col in columns and pd.notna(row[col]):
            location = str(row[col]).strip()
            if location and location != "" and location.lower() not in ['nan', 'none', 'null']:
                return location
    return None

def extract_domain(row, columns):
    """Extrait le domaine d'activité de l'entreprise"""
    possible_columns = [
        'DOMAINE', 'Domaine', 'domaine',
        'ACTIVITE', 'Activité', 'activité',
        'SECTEUR', 'Secteur', 'secteur',
        'SPECIALITE', 'Spécialité', 'spécialité',
        'METIER', 'Métier', 'métier',
        'CORPS METIER', 'Corps métier', 'corps métier',
        'TYPE TRAVAUX', 'Type travaux', 'type travaux',
        'COMPETENCE', 'Compétence', 'compétence'
    ]
    
    for col in possible_columns:
        if col in columns and pd.notna(row[col]):
            domain = str(row[col]).strip()
            if domain and domain != "" and domain.lower() not in ['nan', 'none', 'null']:
                return domain
    
    # Si pas de domaine explicite, essayer de l'inférer depuis le nom
    company_name = extract_company_name(row, columns)
    if company_name:
        name_lower = company_name.lower()
        if any(word in name_lower for word in ['electr', 'élec']):
            return 'Électricité'
        elif any(word in name_lower for word in ['mecani', 'mécan']):
            return 'Mécanique'
        elif any(word in name_lower for word in ['hydraul', 'plomberie']):
            return 'Hydraulique'
        elif any(word in name_lower for word in ['batiment', 'bâtiment', 'construction']):
            return 'Bâtiment'
        elif any(word in name_lower for word in ['maintenance', 'entretien']):
            return 'Maintenance'
    
    return None

def extract_certifications(row, columns):
    """Extrait les certifications de l'entreprise"""
    certifications = []
    
    # Colonnes de certifications possibles
    cert_columns = [
        'MASE', 'Mase', 'mase',
        'ISO 9001', 'ISO9001', 'iso 9001', 'iso9001',
        'ISO 14001', 'ISO14001', 'iso 14001', 'iso14001',
        'QUALIBAT', 'Qualibat', 'qualibat',
        'QUALIBOIS', 'Qualibois', 'qualibois',
        'RGE', 'Rge', 'rge',
        'CERTIFICATION', 'Certification', 'certification',
        'CERTIFICATIONS', 'Certifications', 'certifications'
    ]
    
    for col in cert_columns:
        if col in columns and pd.notna(row[col]):
            value = row[col]
            
            # Si c'est un booléen ou 1/0
            if isinstance(value, bool):
                if value:
                    certifications.append(col.upper())
            elif isinstance(value, (int, float)):
                if value == 1:
                    certifications.append(col.upper())
            elif isinstance(value, str):
                value_clean = value.strip().lower()
                if value_clean in ['oui', 'yes', 'true', '1', 'x']:
                    certifications.append(col.upper())
                elif len(value_clean) > 0 and value_clean not in ['non', 'no', 'false', '0', '-']:
                    # Si c'est du texte descriptif
                    certifications.append(value.strip())
    
    # Rechercher dans les colonnes génériques
    for col in columns:
        if 'certif' in col.lower() and pd.notna(row[col]):
            value = str(row[col]).strip()
            if value and value.lower() not in ['nan', 'none', 'null', 'non', 'no']:
                if value not in certifications:
                    certifications.append(value)
    
    return list(set(certifications))  # Supprimer les doublons

def extract_ca(row, columns):
    """Extrait le chiffre d'affaires"""
    possible_columns = [
        'CA', 'C.A.', 'C.A', 'ca',
        'CHIFFRE AFFAIRES', 'Chiffre affaires', 'chiffre affaires',
        'CHIFFRE D\'AFFAIRES', 'Chiffre d\'affaires', 'chiffre d\'affaires',
        'CA ANNUEL', 'Ca annuel', 'ca annuel',
        'CA HT', 'Ca ht', 'ca ht',
        'TURNOVER', 'Turnover', 'turnover'
    ]
    
    for col in possible_columns:
        if col in columns and pd.notna(row[col]):
            ca_value = row[col]
            
            if isinstance(ca_value, (int, float)):
                if ca_value > 0:
                    return format_ca(ca_value)
            elif isinstance(ca_value, str):
                ca_clean = ca_value.strip()
                if ca_clean and ca_clean.lower() not in ['nan', 'none', 'null']:
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
    possible_columns = [
        'EFFECTIF', 'Effectif', 'effectif',
        'EFFECTIFS', 'Effectifs', 'effectifs',
        'NB SALARIES', 'Nb salariés', 'nb salariés',
        'NOMBRE EMPLOYES', 'Nombre employés', 'nombre employés',
        'PERSONNEL', 'Personnel', 'personnel',
        'SALARIES', 'Salariés', 'salariés'
    ]
    
    for col in possible_columns:
        if col in columns and pd.notna(row[col]):
            emp_value = row[col]
            
            if isinstance(emp_value, (int, float)):
                if emp_value > 0:
                    return str(int(emp_value))
            elif isinstance(emp_value, str):
                emp_clean = emp_value.strip()
                if emp_clean and emp_clean.lower() not in ['nan', 'none', 'null']:
                    # Essayer d'extraire un nombre
                    numbers = re.findall(r'\d+', emp_clean)
                    if numbers:
                        return numbers[0]
                    return emp_clean
    return None

def extract_contact_info(row, columns):
    """Extrait les informations de contact"""
    contact = {}
    
    # Email
    email_columns = ['EMAIL', 'Email', 'email', 'MAIL', 'Mail', 'mail']
    for col in email_columns:
        if col in columns and pd.notna(row[col]):
            email = str(row[col]).strip()
            if '@' in email:
                contact['email'] = email
                break
    
    # Téléphone
    phone_columns = ['TELEPHONE', 'Téléphone', 'téléphone', 'TEL', 'Tel', 'tel', 'PHONE', 'Phone', 'phone']
    for col in phone_columns:
        if col in columns and pd.notna(row[col]):
            phone = str(row[col]).strip()
            if phone and phone.lower() not in ['nan', 'none', 'null']:
                contact['phone'] = phone
                break
    
    return contact if contact else None

def extract_experience(row, columns):
    """Extrait l'expérience ou références"""
    possible_columns = [
        'EXPERIENCE', 'Expérience', 'expérience',
        'REFERENCES', 'Références', 'références',
        'PROJETS', 'Projets', 'projets',
        'REALISATIONS', 'Réalisations', 'réalisations',
        'HISTORIQUE', 'Historique', 'historique'
    ]
    
    for col in possible_columns:
        if col in columns and pd.notna(row[col]):
            exp = str(row[col]).strip()
            if exp and exp.lower() not in ['nan', 'none', 'null']:
                return exp
    return None