# Utility to interact with the Mistral API
# utils/mistral_api.py
import requests
import json
import time

def analyze_document(document_text, api_key):
    """
    Analyser un document avec l'API Mistral pour extraire mots-clés et critères
    
    Args:
        document_text: Texte du document à analyser
        api_key: Clé API Mistral
        
    Returns:
        Résultat de l'analyse (mots-clés, critères)
    """
    url = "https://api.mistral.ai/v1/chat/completions"
    
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
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "system", "content": "Vous êtes un assistant d'analyse de documents d'appel d'offres précis et concis qui répond uniquement au format JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }
    
    # Fonction de retry avec backoff exponentiel
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                
                # Extraire le JSON de la réponse
                try:
                    # Rechercher le premier { et le dernier }
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    
                    if start >= 0 and end > start:
                        json_str = content[start:end]
                        try:
                            result = json.loads(json_str)
                            
                            # Valider et formater les résultats
                            if "selectionCriteria" in result:
                                for i, criterion in enumerate(result["selectionCriteria"]):
                                    # S'assurer que chaque critère a un ID
                                    if "id" not in criterion:
                                        criterion["id"] = i + 1
                                    # S'assurer que chaque critère a un statut de sélection
                                    if "selected" not in criterion:
                                        criterion["selected"] = True
                            
                            if "attributionCriteria" in result:
                                for i, criterion in enumerate(result["attributionCriteria"]):
                                    # S'assurer que chaque critère a un ID
                                    if "id" not in criterion:
                                        criterion["id"] = i + 1
                            
                            return result
                        except json.JSONDecodeError as e:
                            print(f"Erreur de décodage JSON: {e}")
                            print(f"Contenu JSON problématique: {json_str}")
                    
                    # Fallback si le parsing JSON échoue : générer un résultat par défaut
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
                    
                except Exception as e:
                    print(f"Erreur lors de l'analyse du JSON: {e}")
                    raise
            elif response.status_code == 429:  # Too Many Requests
                # Attendre avant de réessayer
                retry_after = int(response.headers.get('Retry-After', retry_delay * (2 ** attempt)))
                print(f"Rate limit atteint, nouvel essai dans {retry_after} secondes...")
                time.sleep(retry_after)
                continue
            else:
                print(f"Erreur API Mistral: {response.status_code}, {response.text}")
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
    
    # Fallback en cas d'échec après tous les essais
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
    Générer le contenu d'un document avec l'API Mistral
    
    Args:
        template_type: Type de document à générer
        data: Données pour le document (projet, entreprises, critères)
        api_key: Clé API Mistral
        
    Returns:
        Contenu du document généré
    """
    url = "https://api.mistral.ai/v1/chat/completions"
    
    # Adapter les instructions en fonction du type de document
    if template_type == "projetMarche":
        document_description = "un projet de marché incluant les clauses administratives et techniques"
    elif template_type == "reglementConsultation":
        document_description = "un règlement de consultation définissant les règles de la consultation"
    elif template_type == "lettreConsultation":
        document_description = "une lettre type pour inviter les entreprises à consulter"
    else:
        document_description = "un document pour la consultation"
    
    # Préparer les données du projet
    project_title = data.get('title', 'Projet EDF')
    cahier_des_charges = data.get('cahierDesCharges', 'Non spécifié')
    selection_criteria = data.get('selectionCriteria', [])
    attribution_criteria = data.get('attributionCriteria', [])
    companies = data.get('companies', [])
    
    # Formater les critères pour le prompt
    selection_criteria_text = "\n".join([f"- {c['name']}: {c.get('description', '')}" for c in selection_criteria if c.get('selected', True)])
    attribution_criteria_text = "\n".join([f"- {c['name']}: {c['weight']}%" for c in attribution_criteria])
    
    # Formater les entreprises pour le prompt
    companies_text = ""
    for i, company in enumerate(companies):
        companies_text += f"Entreprise {i+1}: {company['name']} ({company['location']})\n"
    
    prompt = f"""
    Vous êtes un expert juridique spécialisé dans la rédaction de documents d'appel d'offres pour EDF.
    Veuillez générer {document_description} pour le projet décrit ci-dessous.
    Le document doit être professionnel, complet et conforme aux standards EDF.
    
    INFORMATIONS DU PROJET :
    Titre: {project_title}
    
    Cahier des charges:
    {cahier_des_charges}
    
    Entreprises sélectionnées:
    {companies_text}
    
    Critères de sélection:
    {selection_criteria_text}
    
    Critères d'attribution:
    {attribution_criteria_text}
    
    Génèrez un document complet, structuré et détaillé.
    """
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "system", "content": "Vous êtes un expert juridique spécialisé dans la rédaction de documents d'appel d'offres pour EDF."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            return content
        else:
            print(f"Erreur API Mistral: {response.status_code}, {response.text}")
            # Retourner un contenu par défaut en cas d'erreur
            return f"Document {template_type} pour le projet {project_title}\n\nContenu généré par défaut suite à une erreur."
    except Exception as e:
        print(f"Erreur lors de la génération du document: {e}")
        return f"Document {template_type} pour le projet {project_title}\n\nContenu généré par défaut suite à une erreur."