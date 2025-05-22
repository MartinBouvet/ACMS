import requests
import json
import time
import re

def analyze_document(document_text, api_key):
    """
    Analyse un document avec l'API Prisme AI - Version robuste avec fallback intelligent
    """
    
    print(f"=== ANALYSE DOCUMENT MISTRAL API ===")
    print(f"Longueur du texte: {len(document_text)} caractères")
    
    # Si le document est trop court, utiliser l'analyse basée sur le contenu
    if len(document_text.strip()) < 50:
        print("Document trop court, utilisation de l'analyse par contenu")
        return create_content_based_analysis(document_text)
    
    # Créer un prompt optimisé pour Mistral
    prompt = create_analysis_prompt(document_text)
    
    # Essayer d'abord avec l'API
    try:
        api_result = call_mistral_api(prompt, api_key)
        if api_result:
            print("Analyse réussie via API Mistral")
            return api_result
    except Exception as e:
        print(f"Erreur API Mistral: {e}")
    
    # Fallback: analyse basée sur le contenu du document
    print("Utilisation du fallback - analyse par contenu")
    return create_content_based_analysis(document_text)

def create_analysis_prompt(document_text):
    """Crée un prompt optimisé pour l'analyse"""
    # Limiter la taille du texte pour éviter les timeouts
    text_sample = document_text[:3000] if len(document_text) > 3000 else document_text
    
    return f"""Analysez ce cahier des charges EDF et extrayez UNIQUEMENT le JSON suivant (sans texte supplémentaire):

DOCUMENT:
{text_sample}

Répondez EXACTEMENT avec ce format JSON:
{{
    "keywords": ["mot1", "mot2", "mot3", "mot4", "mot5"],
    "selectionCriteria": [
        {{"id": 1, "name": "Certification MASE", "description": "Certification MASE obligatoire", "selected": true}},
        {{"id": 2, "name": "Expérience technique", "description": "Expérience sur projets similaires", "selected": true}},
        {{"id": 3, "name": "Zone d'intervention", "description": "Capacité d'intervention géographique", "selected": true}}
    ],
    "attributionCriteria": [
        {{"id": 1, "name": "Prix", "weight": 40}},
        {{"id": 2, "name": "Technique", "weight": 35}},
        {{"id": 3, "name": "Délai", "weight": 25}}
    ]
}}"""

def call_mistral_api(prompt, api_key, max_retries=2):
    """Appelle l'API Mistral avec gestion d'erreurs robuste"""
    
    url = "https://api.iag.edf.fr/v2/workspaces/HcA-puQ/webhooks/query"
    headers = {
        "Content-Type": "application/json",
        "knowledge-project-apikey": api_key
    }
    
    data = {
        "text": prompt,
        "projectId": "67f785d59e82260f684a217a"
    }
    
    for attempt in range(max_retries):
        try:
            print(f"Tentative API {attempt + 1}/{max_retries}")
            
            response = requests.post(url, headers=headers, json=data, timeout=45)
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("answer", "")
                
                if content and len(content.strip()) > 10:
                    # Tenter de parser le JSON
                    try:
                        cleaned_content = clean_json_response(content)
                        parsed_result = json.loads(cleaned_content)
                        validated_result = validate_and_fix_response(parsed_result)
                        return validated_result
                    except json.JSONDecodeError as e:
                        print(f"Erreur JSON: {e}")
                        print(f"Contenu reçu: {content[:500]}...")
                        if attempt < max_retries - 1:
                            time.sleep(2)
                            continue
                else:
                    print(f"Réponse vide ou trop courte: {content}")
            else:
                print(f"Erreur HTTP {response.status_code}: {response.text}")
            
            if attempt < max_retries - 1:
                time.sleep(3)
                
        except requests.exceptions.Timeout:
            print(f"Timeout sur tentative {attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(2)
        except Exception as e:
            print(f"Erreur requête: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    return None

def clean_json_response(content):
    """Nettoie la réponse pour extraire le JSON"""
    # Patterns pour extraire le JSON
    patterns = [
        r'```json\s*(.*?)\s*```',
        r'```\s*(.*?)\s*```',
        r'\{.*\}',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1) if 'json' in pattern else match.group(0)
    
    # Si rien trouvé, chercher manuellement
    start = content.find('{')
    end = content.rfind('}') + 1
    if start >= 0 and end > start:
        return content[start:end]
    
    return content.strip()

def validate_and_fix_response(result_data):
    """Valide et corrige la structure de la réponse"""
    if not isinstance(result_data, dict):
        raise ValueError("Réponse invalide")
    
    # Assurer les champs obligatoires
    if "keywords" not in result_data or not isinstance(result_data["keywords"], list):
        result_data["keywords"] = ["EDF", "Projet", "Maintenance", "Intervention"]
    
    if "selectionCriteria" not in result_data or not isinstance(result_data["selectionCriteria"], list):
        result_data["selectionCriteria"] = []
    
    if "attributionCriteria" not in result_data or not isinstance(result_data["attributionCriteria"], list):
        result_data["attributionCriteria"] = []
    
    # Valider selectionCriteria
    for i, criterion in enumerate(result_data["selectionCriteria"]):
        if not isinstance(criterion, dict):
            continue
        if "id" not in criterion:
            criterion["id"] = i + 1
        if "selected" not in criterion:
            criterion["selected"] = True
        if "name" not in criterion:
            criterion["name"] = f"Critère {i + 1}"
        if "description" not in criterion:
            criterion["description"] = "Description à compléter"
    
    # Valider attributionCriteria et ajuster les poids
    total_weight = 0
    for i, criterion in enumerate(result_data["attributionCriteria"]):
        if not isinstance(criterion, dict):
            continue
        if "id" not in criterion:
            criterion["id"] = i + 1
        if "name" not in criterion:
            criterion["name"] = f"Critère {i + 1}"
        if "weight" not in criterion or not isinstance(criterion["weight"], (int, float)):
            criterion["weight"] = 25
        total_weight += criterion["weight"]
    
    # Ajuster les poids pour totaliser 100
    if total_weight != 100 and len(result_data["attributionCriteria"]) > 0:
        if total_weight > 0:
            factor = 100 / total_weight
            for criterion in result_data["attributionCriteria"]:
                criterion["weight"] = round(criterion["weight"] * factor)
        
        # Correction finale
        current_total = sum(c["weight"] for c in result_data["attributionCriteria"])
        if current_total != 100 and result_data["attributionCriteria"]:
            result_data["attributionCriteria"][0]["weight"] += (100 - current_total)
    
    return result_data

def create_content_based_analysis(document_text):
    """
    Crée une analyse intelligente basée sur le contenu réel du document
    """
    print("=== ANALYSE BASÉE SUR LE CONTENU ===")
    
    text_lower = document_text.lower()
    
    # Extraction des mots-clés basée sur le contenu
    keywords = extract_keywords_from_content(text_lower)
    
    # Génération des critères de sélection basés sur le contenu
    selection_criteria = generate_selection_criteria_from_content(text_lower)
    
    # Génération des critères d'attribution adaptatifs
    attribution_criteria = generate_attribution_criteria_from_content(text_lower)
    
    result = {
        "keywords": keywords,
        "selectionCriteria": selection_criteria,
        "attributionCriteria": attribution_criteria
    }
    
    print(f"Mots-clés extraits: {len(keywords)}")
    print(f"Critères sélection: {len(selection_criteria)}")
    print(f"Critères attribution: {len(attribution_criteria)}")
    
    return result

def extract_keywords_from_content(text):
    """Extrait les mots-clés pertinents du document"""
    keywords = []
    
    # Mots-clés techniques spécialisés
    technical_keywords = {
        "échangeur": ["échangeur", "echangeur", "échangeurs"],
        "plaques": ["plaques", "plaque"],
        "nettoyage": ["nettoyage", "nettoyages", "nettoyer", "nettoyant"],
        "maintenance": ["maintenance", "entretien", "réparation"],
        "hydraulique": ["hydraulique", "circuit", "fluide"],
        "thermique": ["thermique", "température", "chaleur"],
        "CNPE": ["cnpe", "centrale nucléaire", "centrale"],
        "Chooz": ["chooz"],
        "intervention": ["intervention", "travaux", "prestation"],
        "sécurité": ["sécurité", "securite", "sûreté", "mase"],
        "qualité": ["qualité", "qualite", "iso", "certification"],
        "délai": ["délai", "delai", "planning", "échéance"]
    }
    
    for keyword, patterns in technical_keywords.items():
        if any(pattern in text for pattern in patterns):
            keywords.append(keyword)
    
    # Si pas assez de mots-clés spécifiques, ajouter des génériques
    if len(keywords) < 4:
        generic_keywords = ["EDF", "Projet", "Technique", "Industriel"]
        keywords.extend(generic_keywords[:4-len(keywords)])
    
    return keywords[:6]  # Limiter à 6 mots-clés

def generate_selection_criteria_from_content(text):
    """Génère des critères de sélection adaptés au contenu"""
    criteria = []
    criteria_id = 1
    
    # Critères de sécurité (toujours prioritaires pour EDF)
    if any(word in text for word in ['nucleaire', 'nucléaire', 'cnpe', 'centrale']):
        criteria.append({
            "id": criteria_id,
            "name": "Habilitation nucléaire",
            "description": "Personnel habilité pour intervention en centrale nucléaire",
            "selected": True
        })
        criteria_id += 1
    
    # Certification MASE (standard EDF)
    criteria.append({
        "id": criteria_id,
        "name": "Certification MASE",
        "description": "Certification MASE obligatoire pour intervention sur site EDF",
        "selected": True
    })
    criteria_id += 1
    
    # Expérience technique spécialisée
    if any(word in text for word in ['échangeur', 'echangeur', 'nettoyage', 'maintenance']):
        criteria.append({
            "id": criteria_id,
            "name": "Expérience technique spécialisée",
            "description": "Expérience confirmée sur équipements similaires (échangeurs, nettoyage)",
            "selected": True
        })
        criteria_id += 1
    
    # Zone géographique
    if 'chooz' in text:
        criteria.append({
            "id": criteria_id,
            "name": "Zone d'intervention Grand-Est",
            "description": "Capacité d'intervention dans la région Grand-Est (Chooz - Ardennes)",
            "selected": True
        })
    else:
        criteria.append({
            "id": criteria_id,
            "name": "Zone d'intervention",
            "description": "Capacité d'intervention sur la zone du projet",
            "selected": True
        })
    criteria_id += 1
    
    # Capacité technique
    criteria.append({
        "id": criteria_id,
        "name": "Capacité technique",
        "description": "Moyens techniques et humains adaptés au projet",
        "selected": True
    })
    criteria_id += 1
    
    # Références similaires
    criteria.append({
        "id": criteria_id,
        "name": "Références sur projets similaires",
        "description": "Références récentes sur des projets de nature similaire",
        "selected": True
    })
    
    return criteria

def generate_attribution_criteria_from_content(text):
    """Génère des critères d'attribution adaptés au contenu"""
    criteria = []
    
    # Analyser le type de projet pour adapter les pondérations
    is_technical_project = any(word in text for word in ['technique', 'technologique', 'spécialisé', 'complexe'])
    is_safety_critical = any(word in text for word in ['nucleaire', 'nucléaire', 'sécurité', 'sûreté'])
    is_maintenance = any(word in text for word in ['maintenance', 'entretien', 'nettoyage'])
    
    # Valeur technique (toujours importante)
    technical_weight = 45 if is_technical_project else 40
    criteria.append({
        "id": 1,
        "name": "Valeur technique",
        "weight": technical_weight
    })
    
    # Prix (important mais pas prioritaire sur technique)
    price_weight = 25 if is_technical_project else 30
    criteria.append({
        "id": 2,
        "name": "Prix",
        "weight": price_weight
    })
    
    # Délai
    delay_weight = 15 if is_maintenance else 20
    criteria.append({
        "id": 3,
        "name": "Délai",
        "weight": delay_weight
    })
    
    # Sécurité/Qualité
    safety_weight = 15 if is_safety_critical else 10
    criteria.append({
        "id": 4,
        "name": "Sécurité et Qualité",
        "weight": safety_weight
    })
    
    # Vérifier que le total fait 100
    total = sum(c["weight"] for c in criteria)
    if total != 100:
        criteria[0]["weight"] += (100 - total)
    
    return criteria

def generate_document(template_type, data, api_key):
    """Génère un document avec l'API Prisme AI - Version robuste"""
    
    print(f"=== GÉNÉRATION DOCUMENT ===")
    print(f"Type: {template_type}")
    
    # Construire le prompt selon le type de document
    prompt = build_document_prompt(template_type, data)
    
    # Essayer avec l'API
    try:
        result = call_mistral_api_for_document(prompt, api_key)
        if result:
            return result
    except Exception as e:
        print(f"Erreur génération API: {e}")
    
    # Fallback: génération de base
    return generate_fallback_document(template_type, data)

def build_document_prompt(template_type, data):
    """Construit le prompt pour la génération de document"""
    
    doc_descriptions = {
        "projetMarche": "un projet de marché (clauses administratives et techniques)",
        "reglementConsultation": "un règlement de consultation",
        "lettreConsultation": "une lettre de consultation",
        "grilleEvaluation": "une grille d'évaluation avec les critères"
    }
    
    doc_type = doc_descriptions.get(template_type, "un document")
    
    project_title = data.get('title', 'Projet EDF')
    project_description = data.get('description', '')
    
    return f"""Générez {doc_type} professionnel pour EDF.

PROJET: {project_title}
DESCRIPTION: {project_description}

Le document doit être structuré, professionnel et conforme aux standards EDF.
Répondez directement avec le contenu du document sans préambule."""

def call_mistral_api_for_document(prompt, api_key):
    """Appelle l'API pour la génération de document"""
    
    url = "https://api.iag.edf.fr/v2/workspaces/HcA-puQ/webhooks/query"
    headers = {
        "Content-Type": "application/json",
        "knowledge-project-apikey": api_key
    }
    
    data = {
        "text": prompt,
        "projectId": "67f785d59e82260f684a217a"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("answer", "")
            if content and len(content.strip()) > 50:
                return content
        
        print(f"Erreur API document: {response.status_code}")
        return None
        
    except Exception as e:
        print(f"Erreur requête document: {e}")
        return None

def generate_fallback_document(template_type, data):
    """Génère un document de base en cas d'échec de l'API"""
    
    project_title = data.get('title', 'Projet EDF')
    project_description = data.get('description', '')
    
    fallback_templates = {
        "projetMarche": f"""PROJET DE MARCHÉ

Objet: {project_title}

1. OBJET DU MARCHÉ
{project_description}

2. DESCRIPTION DES PRESTATIONS
Les prestations comprennent l'ensemble des travaux, fournitures et services nécessaires.

3. CLAUSES TECHNIQUES
- Respect des normes en vigueur
- Certification des intervenants
- Respect des consignes de sécurité

4. CLAUSES ADMINISTRATIVES
- Durée d'exécution: À définir
- Modalités de paiement: Selon conditions générales EDF
- Garanties: Selon réglementation""",

        "reglementConsultation": f"""RÈGLEMENT DE CONSULTATION

Objet: {project_title}

1. MODALITÉS DE LA CONSULTATION
Cette consultation est lancée selon la procédure adaptée.

2. CONTENU DU DOSSIER
- Présent règlement
- Cahier des charges
- Projet de marché

3. CRITÈRES D'ATTRIBUTION
- Valeur technique
- Prix
- Délai
- Sécurité

4. REMISE DES OFFRES
Date limite: À définir
Modalités: Dépôt en ligne ou courrier""",

        "lettreConsultation": f"""LETTRE DE CONSULTATION

Objet: {project_title}

Madame, Monsieur,

EDF vous invite à présenter une offre pour le projet suivant:
{project_description}

Votre entreprise a été présélectionnée pour participer à cette consultation.

Merci de nous faire parvenir votre offre avant la date limite.

Cordialement,
Équipe Achats EDF""",

        "grilleEvaluation": f"""GRILLE D'ÉVALUATION

Projet: {project_title}

CRITÈRES D'ÉVALUATION:

1. Valeur technique (40%)
   - Méthodologie
   - Moyens techniques
   - Compétences équipe

2. Prix (30%)
   - Prix global
   - Détail des coûts

3. Délai (20%)
   - Planning proposé
   - Respect échéances

4. Sécurité (10%)
   - Certifications
   - Procédures sécurité"""
    }
    
    return fallback_templates.get(template_type, f"Document {template_type} pour {project_title}")

def get_agent_answer(question, api_key, agent_id):
    """Interroge l'agent Prisme AI avec gestion d'erreurs"""
    
    try:
        response = call_mistral_api(question, api_key)
        if response:
            return str(response)
        else:
            return "Désolé, je n'ai pas pu obtenir de réponse."
    except Exception as e:
        return f"Erreur: {str(e)}"