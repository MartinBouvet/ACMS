import requests
import json
import time
import re

def analyze_document(document_text, api_key):
    """
    Analyse un document avec l'API Prisme AI (Mistral)
    
    Args:
        document_text: Texte du document à analyser
        api_key: Clé API pour Prisme AI
        
    Returns:
        Dictionnaire avec les critères et mots-clés extraits
    """
    url = "https://api.iag.edf.fr/v2/workspaces/HcA-puQ/webhooks/query"
    
    prompt = f"""
    Vous êtes un assistant expert d'EDF qui analyse des cahiers des charges pour des projets <400K euros. 
    Votre tâche est d'extraire les informations importantes du document suivant.
    
    Voici le cahier des charges :
    ```
    {document_text}
    ```
    
    Veuillez extraire et fournir les informations suivantes au format JSON :
    1. Mots-clés : Identifiez 5 à 8 mots ou phrases clés qui caractérisent le projet.
    2. Critères de sélection : Proposez 4 à 6 critères pertinents pour sélectionner des entreprises (expérience, certifications requises, zone d'intervention, capacité de production, etc.)
    3. Critères d'attribution : Suggérez une répartition en pourcentage des critères d'attribution (qualité technique, coût, délais, sécurité, etc.). Le total doit être égal à 100%.
    
    Pour chaque critère de sélection, incluez:
    - Un identifiant unique (id)
    - Un nom clair (name)
    - Une description détaillée (description)
    - Un statut de sélection par défaut (selected: true)
    
    Pour chaque critère d'attribution, incluez:
    - Un identifiant unique (id)
    - Un nom clair (name)
    - Une pondération en pourcentage (weight)
    
    Répondez uniquement avec un objet JSON valide.
    """
    
    headers = {
        "Content-Type": "application/json",
        "knowledge-project-apikey": api_key
    }
    
    data = {
        "text": prompt,
        "projectId": "67f785d59e82260f684a217a"  # ID de l'agent
    }
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("answer", "")
                
                try:
                    # Extraire le JSON de la réponse
                    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                    else:
                        # Chercher directement un objet JSON dans la réponse
                        start = content.find('{')
                        end = content.rfind('}') + 1
                        if start >= 0 and end > start:
                            json_str = content[start:end]
                        else:
                            raise ValueError("Format JSON non détecté dans la réponse")
                    
                    result_data = json.loads(json_str)
                    
                    # Vérifier et ajouter les champs manquants
                    if "selectionCriteria" in result_data:
                        for i, criterion in enumerate(result_data["selectionCriteria"]):
                            if "id" not in criterion:
                                criterion["id"] = i + 1
                            if "selected" not in criterion:
                                criterion["selected"] = True
                    
                    if "attributionCriteria" in result_data:
                        for i, criterion in enumerate(result_data["attributionCriteria"]):
                            if "id" not in criterion:
                                criterion["id"] = i + 1
                    
                    return result_data
                except (ValueError, json.JSONDecodeError) as e:
                    print(f"Erreur de décodage JSON: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
            elif response.status_code == 401:
                print(f"Erreur d'authentification API Prisme AI: {response.status_code}, {response.text}")
                raise Exception(f"Erreur d'authentification: Vérifiez votre clé API")
            else:
                print(f"Erreur API Prisme AI: {response.status_code}, {response.text}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                raise Exception(f"API error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Erreur de requête: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))
                continue
            raise
    
    # En cas d'échec après plusieurs tentatives, retourner un résultat par défaut
    return {
        "keywords": ["Projet EDF", "Travaux", "Maintenance", "Sous-traitance", "Sécurité"],
        "selectionCriteria": [
            {"id": 1, "name": "Certification MASE", "description": "L'entreprise doit posséder la certification MASE", "selected": True},
            {"id": 2, "name": "Expérience similaire", "description": "Au moins 3 projets similaires réalisés", "selected": True},
            {"id": 3, "name": "Zone d'intervention", "description": "Capacité d'intervention dans la région concernée", "selected": True},
            {"id": 4, "name": "Capacité technique", "description": "Ressources suffisantes pour réaliser le projet", "selected": True}
        ],
        "attributionCriteria": [
            {"id": 1, "name": "Valeur technique", "weight": 40},
            {"id": 2, "name": "Prix", "weight": 30},
            {"id": 3, "name": "Délai d'exécution", "weight": 20},
            {"id": 4, "name": "Performance sécurité", "weight": 10}
        ]
    }

def generate_document(template_type, data, api_key):
    """
    Génère un document à partir d'un template avec l'API Prisme AI
    
    Args:
        template_type: Type de document à générer
        data: Données pour le document
        api_key: Clé API pour Prisme AI
        
    Returns:
        Contenu du document généré
    """
    url = "https://api.iag.edf.fr/v2/workspaces/HcA-puQ/webhooks/query"
    
    if template_type == "projetMarche":
        document_description = "un projet de marché incluant les clauses administratives et techniques"
    elif template_type == "reglementConsultation":
        document_description = "un règlement de consultation définissant les règles de la consultation"
    elif template_type == "lettreConsultation":
        document_description = "une lettre type pour inviter les entreprises à consulter"
    elif template_type == "grilleEvaluation":
        document_description = "une grille d'évaluation basée sur les critères d'attribution"
    else:
        document_description = "un document pour la consultation"
    
    project_title = data.get('title', 'Projet EDF')
    project_description = data.get('description', '')
    cahier_des_charges = data.get('cahierDesCharges', 'Non spécifié')
    selection_criteria = data.get('selectionCriteria', [])
    attribution_criteria = data.get('attributionCriteria', [])
    companies = data.get('companies', [])
    
    selection_criteria_text = "\n".join([f"- {c['name']}: {c.get('description', '')}" for c in selection_criteria if c.get('selected', True)])
    attribution_criteria_text = "\n".join([f"- {c['name']}: {c['weight']}%" for c in attribution_criteria])
    
    companies_text = ""
    for i, company in enumerate(companies):
        if company.get('selected', True):
            companies_text += f"Entreprise {i+1}: {company['name']} ({company['location']})\n"
            if company.get('certifications'):
                companies_text += f"  Certifications: {', '.join(company['certifications'])}\n"
            if company.get('ca'):
                companies_text += f"  Chiffre d'affaires: {company['ca']}\n"
            if company.get('employees'):
                companies_text += f"  Effectifs: {company['employees']}\n"
    
    prompt = f"""
    Vous êtes un expert juridique spécialisé dans la rédaction de documents d'appel d'offres pour EDF.
    Veuillez générer {document_description} pour le projet décrit ci-dessous.
    Le document doit être professionnel, complet et conforme aux standards EDF.
    
    INFORMATIONS DU PROJET :
    Titre: {project_title}
    Description: {project_description}
    
    Cahier des charges:
    {cahier_des_charges}
    
    Entreprises sélectionnées:
    {companies_text}
    
    Critères de sélection:
    {selection_criteria_text}
    
    Critères d'attribution:
    {attribution_criteria_text}
    
    Génèrez un document complet, structuré et détaillé au format approprié.
    """
    
    if template_type == "grilleEvaluation":
        prompt += """
        Pour la grille d'évaluation, créez un tableau avec les colonnes suivantes:
        - Critère
        - Pondération (%)
        - Note (sur 10)
        - Note pondérée
        - Remarques
        
        Incluez des lignes pour chaque critère d'attribution et des lignes pour les totaux.
        """
    
    headers = {
        "Content-Type": "application/json",
        "knowledge-project-apikey": api_key
    }
    
    data = {
        "text": prompt,
        "projectId": "67f785d59e82260f684a217a"  # ID de l'agent
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("answer", "")
            return content
        else:
            print(f"Erreur API Prisme AI: {response.status_code}, {response.text}")
            return f"Document {template_type} pour le projet {project_title}\n\nContenu généré par défaut suite à une erreur."
    except Exception as e:
        print(f"Erreur lors de la génération du document: {e}")
        return f"Document {template_type} pour le projet {project_title}\n\nContenu généré par défaut suite à une erreur."

def get_agent_answer(question, api_key, agent_id):
    """
    Interroge l'agent Prisme AI
    
    Args:
        question: Question à poser
        api_key: Clé API pour Prisme AI
        agent_id: ID de l'agent
        
    Returns:
        Réponse de l'agent
    """
    url = "https://api.iag.edf.fr/v2/workspaces/HcA-puQ/webhooks/query"
    
    headers = {
        "Content-Type": "application/json",
        "knowledge-project-apikey": api_key
    }
    
    data = {
        "text": question,
        "projectId": agent_id
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("answer", "")
            return content
        else:
            print(f"Erreur API Prisme AI: {response.status_code}, {response.text}")
            return "Désolé, je n'ai pas pu obtenir de réponse de l'agent Prisme AI."
    except Exception as e:
        print(f"Erreur lors de l'interrogation de l'agent: {e}")
        return f"Erreur: {str(e)}"