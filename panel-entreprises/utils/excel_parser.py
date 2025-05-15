# Utility to parse Excel files
# utils/excel_parser.py
import pandas as pd
import os

def load_companies_from_excel(file_path):
    """
    Charge les entreprises depuis le fichier Excel ACMS
    
    Args:
        file_path: Chemin vers le fichier Excel
        
    Returns:
        Liste des entreprises au format attendu par l'application
    """
    try:
        print(f"Tentative de chargement du fichier: {file_path}")
        
        # Vérifier si le fichier existe
        if not os.path.exists(file_path):
            print(f"Fichier non trouvé: {file_path}")
            return []
            
        # Charger le fichier Excel
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Afficher les colonnes pour le débogage
        print("Colonnes trouvées dans le fichier Excel:")
        print(df.columns.tolist())
        
        companies = []
        
        # Parcourir les lignes et extraire les données
        for idx, row in df.iterrows():
            try:
                # Créer un identifiant unique
                company_id = str(idx + 1).zfill(3)
                
                # Extraire le nom de l'entreprise (adapter selon la structure réelle du fichier)
                company_name = get_value(row, ['RAISON SOCIALE', 'Entreprise', 'Nom'])
                
                # Extraire la localisation
                location = get_value(row, ['Ville', 'Localisation', 'Adresse'])
                
                # Extraire les certifications (adapter selon la structure réelle)
                certifications = []
                cert_columns = ['MASE', 'ISO 9001', 'ISO 14001', 'QUALIBAT']
                
                for cert in cert_columns:
                    if cert in df.columns and pd.notna(row[cert]) and row[cert] not in ['Non', 'non', 0, '0', False]:
                        certifications.append(cert)
                
                # Extraire d'autres informations
                ca = get_value(row, ['CA', 'Chiffre d\'affaires', 'CHIFFRE D\'AFFAIRES'])
                employees = get_value(row, ['Effectifs', 'EFFECTIF', 'Nombre d\'employés'])
                experience = get_value(row, ['Expérience', 'EXPERIENCE', 'Projets similaires'])
                
                # Créer l'objet entreprise
                company = {
                    'id': company_id,
                    'name': str(company_name) if company_name is not None else f"Entreprise {company_id}",
                    'location': str(location) if location is not None else 'Non spécifié',
                    'certifications': certifications,
                    'ca': str(ca) if ca is not None else 'Non spécifié',
                    'employees': str(employees) if employees is not None else 'Non spécifié',
                    'experience': str(experience) if experience is not None else 'Non spécifié'
                }
                
                companies.append(company)
            except Exception as e:
                print(f"Erreur lors du traitement de la ligne {idx}: {e}")
                continue
        
        print(f"Nombre d'entreprises extraites: {len(companies)}")
        return companies
    except Exception as e:
        print(f"Erreur lors du chargement du fichier Excel: {e}")
        import traceback
        print(traceback.format_exc())
        return []

def get_value(row, possible_columns):
    """
    Récupère la première valeur non nulle parmi plusieurs colonnes possibles
    
    Args:
        row: Ligne du DataFrame
        possible_columns: Liste des noms de colonnes possibles
        
    Returns:
        Valeur trouvée ou None
    """
    for col in possible_columns:
        if col in row.index and pd.notna(row[col]):
            return row[col]
    return None