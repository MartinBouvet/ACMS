import pandas as pd
import os
import re

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
                
                # Extraire le nom de l'entreprise (vérifier différentes possibilités de noms de colonnes)
                company_name = None
                for col in ['RAISON SOCIALE', 'Entreprise', 'Nom', 'NOM ENTREPRISE', 'ENTREPRISE', 'DENOMINATION']:
                    if col in df.columns and pd.notna(row[col]):
                        company_name = str(row[col]).strip()
                        break
                
                if not company_name:
                    company_name = f"Entreprise {company_id}"
                
                # Extraire la localisation
                location = None
                for col in ['Ville', 'Localisation', 'Adresse', 'VILLE', 'ADRESSE', 'LOCALITE']:
                    if col in df.columns and pd.notna(row[col]):
                        location = str(row[col]).strip()
                        break
                
                if not location:
                    location = 'Non spécifié'
                
                # Extraire les certifications
                certifications = []
                cert_columns = ['MASE', 'ISO 9001', 'ISO 14001', 'QUALIBAT', 'CERTIFICATION']
                
                for cert in cert_columns:
                    if cert in df.columns and pd.notna(row[cert]) and row[cert] not in ['Non', 'non', 0, '0', False]:
                        certifications.append(cert)
                
                # Vérifier aussi les colonnes contenant "CERTIF"
                for col in df.columns:
                    if 'CERTIF' in col.upper() and pd.notna(row[col]) and row[col] not in ['Non', 'non', 0, '0', False]:
                        if isinstance(row[col], str) and len(row[col].strip()) > 0:
                            certifications.append(row[col].strip())
                        elif row[col] == 1 or row[col] is True:
                            certifications.append(col)
                
                # Extraire le chiffre d'affaires
                ca = None
                for col in ['CA', 'Chiffre d\'affaires', 'CHIFFRE D\'AFFAIRES', 'CA ANNUEL', 'CA HT']:
                    if col in df.columns and pd.notna(row[col]):
                        if isinstance(row[col], (int, float)):
                            if row[col] > 1000000:  # Supposer que c'est en euros
                                ca = f"{row[col]/1000000:.1f}M€"
                            elif row[col] > 1000:
                                ca = f"{row[col]/1000:.0f}k€"
                            else:
                                ca = f"{row[col]:.0f}€"
                        else:
                            ca = str(row[col])
                        break
                
                # Extraire les effectifs
                employees = None
                for col in ['Effectifs', 'EFFECTIF', 'Nombre d\'employés', 'NB SALARIES', 'PERSONNEL']:
                    if col in df.columns and pd.notna(row[col]):
                        if isinstance(row[col], (int, float)):
                            employees = str(int(row[col]))
                        else:
                            # Tenter d'extraire un nombre de la valeur texte
                            matches = re.findall(r'\d+', str(row[col]))
                            if matches:
                                employees = matches[0]
                            else:
                                employees = str(row[col])
                        break
                
                # Extraire l'expérience ou projets similaires
                experience = None
                for col in ['Expérience', 'EXPERIENCE', 'Projets similaires', 'REFERENCES', 'PROJETS']:
                    if col in df.columns and pd.notna(row[col]):
                        experience = str(row[col])
                        break
                
                # Créer l'objet entreprise
                company = {
                    'id': company_id,
                    'name': company_name,
                    'location': location,
                    'certifications': certifications,
                    'ca': ca if ca is not None else 'Non spécifié',
                    'employees': employees if employees is not None else 'Non spécifié',
                    'experience': experience if experience is not None else 'Non spécifié'
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