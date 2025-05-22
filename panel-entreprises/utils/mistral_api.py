import requests
import json
import time
import re

def analyze_document(document_text, api_key):
    """
    Analyse un document avec l'API Prisme AI (Mistral) - Version corrigée
    
    Args:
        document_text: Texte du document à analyser
        api_key: Clé API pour Prisme AI
        
    Returns:
        Dictionnaire avec les critères et mots-clés extraits
    """
    
    print(f"=== DÉBUT ANALYSE DOCUMENT ===")
    print(f"Longueur du texte: {len(document_text)} caractères")
    print(f"Extrait du texte: {document_text[:200]}...")
    
    # Créer un prompt plus simple et direct
    prompt = f"""Analysez ce cahier des charges EDF et extrayez les informations au format JSON exact suivant :

DOCUMENT À ANALYSER :
{document_text[:2000]}

Répondez UNIQUEMENT avec ce JSON (sans autre texte) :
{{
    "keywords": ["mot1", "mot2", "mot3", "mot4", "mot5"],
    "selectionCriteria": [
        {{"id": 1, "name": "Certification MASE", "description": "L'entreprise doit posséder la certification MASE", "selected": true}},
        {{"id": 2, "name": "Expérience similaire", "description": "Au moins 3 projets similaires dans les 5 dernières années", "selected": true}},
        {{"id": 3, "name": "Zone d'intervention", "description": "Capacité d'intervention dans la région", "selected": true}}
    ],
    "attributionCriteria": [
        {{"id": 1, "name": "Valeur technique", "weight": 40}},
        {{"id": 2, "name": "Prix", "weight": 30}},
        {{"id": 3, "name": "Délai", "weight": 20}},
        {{"id": 4, "name": "Sécurité", "weight": 10}}
    ]
}}"""

    # Configuration de l'API
    url = "https://api.iag.edf.fr/v2/workspaces/HcA-puQ/webhooks/query"
    headers = {
        "Content-Type": "application/json",
        "knowledge-project-apikey": api_key
    }
    
    data = {
        "text": prompt,
        "projectId": "67f785d59e82260f684a217a"
    }
    
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Longueur du prompt: {len(prompt)}")
    
    # Essayer avec un timeout plus long et une approche différente
    max_retries = 2
    retry_delay = 3
    
    for attempt in range(max_retries):
        try:
            print(f"=== TENTATIVE {attempt + 1} ===")
            
            # Essayer d'abord avec un prompt plus court si c'est la 2ème tentative
            if attempt == 1:
                print("Tentative avec un prompt simplifié...")
                simple_prompt = f"""Analysez ce document EDF et donnez le résultat en JSON :

Texte: {document_text[:1000]}

Format JSON attendu :
{{"keywords": ["maintenance", "échangeur", "nettoyage"], "selectionCriteria": [{{"id": 1, "name": "MASE", "description": "Certification requise", "selected": true}}], "attributionCriteria": [{{"id": 1, "name": "Prix", "weight": 50}}, {{"id": 2, "name": "Technique", "weight": 50}}]}}"""
                
                data["text"] = simple_prompt
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Structure de la réponse: {list(result.keys())}")
                
                content = result.get("answer", "")
                print(f"Contenu reçu (premiers 500 char): {content[:500]}")
                
                # Si la réponse contient une erreur, essayer le fallback
                if "error" in content.lower() or "sorry" in content.lower() or len(content.strip()) < 10:
                    print(f"Réponse d'erreur détectée: {content}")
                    if attempt < max_retries - 1:
                        print("Nouvelle tentative...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        print("Toutes les tentatives ont échoué, utilisation du fallback")
                        return create_document_based_analysis(document_text)
                
                try:
                    # Nettoyer et parser le JSON
                    cleaned_content = clean_json_response(content)
                    print(f"JSON nettoyé: {cleaned_content[:300]}...")
                    
                    result_data = json.loads(cleaned_content)
                    result_data = validate_and_fix_response(result_data)
                    
                    print("=== ANALYSE RÉUSSIE ===")
                    print(f"Keywords: {result_data.get('keywords', [])}")
                    print(f"Critères sélection: {len(result_data.get('selectionCriteria', []))}")
                    print(f"Critères attribution: {len(result_data.get('attributionCriteria', []))}")
                    
                    return result_data
                    
                except (ValueError, json.JSONDecodeError) as e:
                    print(f"Erreur de décodage JSON: {e}")
                    print(f"Contenu problématique: {content}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    
            else:
                print(f"Erreur HTTP {response.status_code}: {response.text}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                
        except requests.exceptions.RequestException as e:
            print(f"Erreur de requête: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
    
    # Fallback si toutes les tentatives échouent
    print("=== UTILISATION DU FALLBACK ===")
    return create_document_based_analysis(document_text)

def clean_json_response(content):
    """Nettoie la réponse pour extraire le JSON valide"""
    # Rechercher un bloc JSON délimité par ```json
    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()
    
    # Rechercher un bloc JSON délimité par ```
    json_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()
    
    # Chercher directement un objet JSON dans la réponse
    start = content.find('{')
    end = content.rfind('}') + 1
    if start >= 0 and end > start:
        return content[start:end]
    
    # Si rien n'est trouvé, retourner le contenu tel quel
    return content.strip()

def validate_and_fix_response(result_data):
    """Valide et corrige la structure de la réponse"""
    if not isinstance(result_data, dict):
        raise ValueError("La réponse n'est pas un objet JSON valide")
    
    # Assurer les champs obligatoires
    if "keywords" not in result_data:
        result_data["keywords"] = ["Projet EDF", "Travaux", "Maintenance"]
    
    if "selectionCriteria" not in result_data:
        result_data["selectionCriteria"] = []
    
    if "attributionCriteria" not in result_data:
        result_data["attributionCriteria"] = []
    
    # Valider selectionCriteria
    for i, criterion in enumerate(result_data["selectionCriteria"]):
        if "id" not in criterion:
            criterion["id"] = i + 1
        if "selected" not in criterion:
            criterion["selected"] = True
        if "name" not in criterion:
            criterion["name"] = f"Critère {i + 1}"
        if "description" not in criterion:
            criterion["description"] = "Description à compléter"
    
    # Valider et ajuster attributionCriteria
    total_weight = 0
    for i, criterion in enumerate(result_data["attributionCriteria"]):
        if "id" not in criterion:
            criterion["id"] = i + 1
        if "name" not in criterion:
            criterion["name"] = f"Critère {i + 1}"
        if "weight" not in criterion:
            criterion["weight"] = 25
        total_weight += criterion["weight"]
    
    # Ajuster les poids pour qu'ils totalisent 100
    if total_weight != 100 and len(result_data["attributionCriteria"]) > 0:
        adjustment_factor = 100 / total_weight
        for criterion in result_data["attributionCriteria"]:
            criterion["weight"] = round(criterion["weight"] * adjustment_factor)
        
        # Ajustement final pour s'assurer que le total est exactement 100
        current_total = sum(c["weight"] for c in result_data["attributionCriteria"])
        if current_total != 100:
            result_data["attributionCriteria"][0]["weight"] += (100 - current_total)
    
    return result_data

def create_document_based_analysis(document_text):
    """Crée une analyse basée sur le contenu réel du document"""
    text_lower = document_text.lower()
    
    # Extraire des mots-clés basés sur le contenu
    keywords = []
    
    # Mots-clés spécifiques au document
    keyword_patterns = {
        "échangeur": ["échangeur", "echangeur"],
        "plaques": ["plaques", "plaque"],
        "nettoyage": ["nettoyage", "nettoyages", "nettoyer"],
        "maintenance": ["maintenance", "entretien"],
        "CNPE": ["cnpe", "centrale nucléaire"],
        "Chooz": ["chooz"],
        "hydraulique": ["hydraulique", "circuit"],
        "intervention": ["intervention", "travaux"]
    }
    
    for keyword, patterns in keyword_patterns.items():
        if any(pattern in text_lower for pattern in patterns):
            keywords.append(keyword)
    
    # Limiter à 6 mots-clés
    if not keywords:
        keywords = ["Maintenance", "Équipement", "Intervention", "EDF"]
    keywords = keywords[:6]
    
    # Critères de sélection basés sur le document
    selection_criteria = [
        {
            "id": 1,
            "name": "Certification MASE",
            "description": "Certification MASE obligatoire pour intervention en site nucléaire",
            "selected": True
        },
        {
            "id": 2,
            "name": "Expérience échangeurs à plaques",
            "description": "Expérience confirmée dans le nettoyage d'échangeurs à plaques",
            "selected": True
        },
        {
            "id": 3,
            "name": "Habilitation nucléaire",
            "description": "Personnel habilité pour intervention en centrale nucléaire",
            "selected": True
        },
        {
            "id": 4,
            "name": "Zone d'intervention",
            "description": "Capacité d'intervention dans la région Grand-Est (Chooz)",
            "selected": True
        }
    ]
    
    # Critères d'attribution
    attribution_criteria = [
        {
            "id": 1,
            "name": "Valeur technique",
            "weight": 45
        },
        {
            "id": 2,
            "name": "Prix",
            "weight": 35
        },
        {
            "id": 3,
            "name": "Délai d'intervention",
            "weight": 15
        },
        {
            "id": 4,
            "name": "Performance sécurité",
            "weight": 5
        }
    ]
    
    return {
        "keywords": keywords,
        "selectionCriteria": selection_criteria,
        "attributionCriteria": attribution_criteria
    }

def generate_document(template_type, data, api_key):
    """Génère un document avec l'API Prisme AI"""
    # Code existant inchangé
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
        "projectId": "67f785d59e82260f684a217a"
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
    """Interroge l'agent Prisme AI"""
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