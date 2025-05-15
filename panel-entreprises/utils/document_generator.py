import os
import time
from datetime import datetime
from utils.mistral_api import generate_document

def create_document(template_type, project_data, companies, output_dir, api_key):
    """
    Crée un document à partir d'un template et des données du projet
    
    Args:
        template_type: Type de document à générer
        project_data: Données du projet
        companies: Entreprises sélectionnées
        output_dir: Répertoire de sortie
        api_key: Clé API Mistral
        
    Returns:
        Informations sur le document généré
    """
    try:
        # Créer le répertoire de sortie s'il n'existe pas
        os.makedirs(output_dir, exist_ok=True)
        
        # Générer le contenu du document avec l'API Mistral
        content = generate_document(template_type, {
            'title': project_data.get('title', 'Projet EDF'),
            'description': project_data.get('description', ''),
            'cahierDesCharges': project_data.get('cahierDesCharges', ''),
            'selectionCriteria': project_data.get('selectionCriteria', []),
            'attributionCriteria': project_data.get('attributionCriteria', []),
            'companies': companies
        }, api_key)
        
        # Créer un nom de fichier unique
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        project_id = project_data.get('id', 'projet').replace(' ', '_')
        
        # Déterminer l'extension du fichier
        if template_type == 'grilleEvaluation':
            extension = 'xlsx'
        else:
            extension = 'docx'
        
        # Créer un préfixe selon le type de document
        prefix_map = {
            'projetMarche': 'PM',
            'reglementConsultation': 'RC',
            'grilleEvaluation': 'GE',
            'lettreConsultation': 'LC'
        }
        prefix = prefix_map.get(template_type, 'DOC')
        
        # Construire le nom du fichier
        filename = f"{prefix}_{project_id}_{timestamp}.{extension}"
        file_path = os.path.join(output_dir, filename)
        
        # Écrire le contenu dans un fichier
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            'fileName': filename,
            'fileUrl': f"/api/documents/download/{filename}",
            'type': extension
        }
    except Exception as e:
        print(f"Erreur lors de la création du document: {e}")
        raise