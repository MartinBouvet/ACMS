"""
mistral_api.py - Enhanced Mistral API integration for EDF Panel Entreprises
"""

import requests
import json
import time
import re
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MistralAPI:
    """Wrapper for Mistral API with enhanced error handling and retry logic"""
    
    def __init__(self, api_key, agent_id):
        self.api_key = api_key
        self.agent_id = agent_id
        self.api_url = "https://api.iag.edf.fr/v2/workspaces/HcA-puQ/webhooks/query"
        self.max_retries = 3
        self.retry_delay = 2  # seconds
    
    def analyze_document(self, document_text):
        """
        Analyze a document to extract criteria and keywords
        
        Args:
            document_text: Text content of the document to analyze
            
        Returns:
            Dictionary with keywords, selection criteria, and attribution criteria
        """
        logger.info("=== ANALYZING DOCUMENT WITH MISTRAL API ===")
        logger.info(f"Document length: {len(document_text)} characters")
        
        # For very short texts, use fallback
        if len(document_text.strip()) < 100:
            logger.warning("Document too short, using fallback analysis")
            return self._create_fallback_analysis()
        
        # Create analysis prompt
        prompt = self._create_analysis_prompt(document_text)
        
        # Call API with retries
        result = self._call_api(prompt)
        
        if result:
            try:
                # Parse and validate the response
                parsed_result = self._parse_analysis_response(result)
                if parsed_result:
                    logger.info("Analysis successful")
                    logger.info(f"Keywords: {len(parsed_result.get('keywords', []))} extracted")
                    logger.info(f"Selection criteria: {len(parsed_result.get('selectionCriteria', []))} extracted")
                    logger.info(f"Attribution criteria: {len(parsed_result.get('attributionCriteria', []))} extracted")
                    return parsed_result
            except Exception as e:
                logger.error(f"Error parsing analysis response: {e}")
        
        # If API call fails or returns invalid response, use fallback
        logger.warning("Using fallback analysis")
        return self._create_fallback_analysis(document_text)
    
    def generate_document(self, template_type, project_data, selected_companies=None):
        """
        Generate a document based on template type and project data
        
        Args:
            template_type: Type of document to generate
            project_data: Dictionary with project information
            selected_companies: List of selected companies
            
        Returns:
            Generated document content
        """
        logger.info(f"=== GENERATING DOCUMENT: {template_type} ===")
        
        # Create document generation prompt
        prompt = self._create_document_prompt(template_type, project_data, selected_companies)
        
        # Call API with retries
        result = self._call_api(prompt)
        
        if result:
            # Clean up and format the result
            document_content = self._format_document_content(result, template_type)
            
            if document_content:
                logger.info(f"Document generated successfully, length: {len(document_content)} characters")
                return document_content
        
        # Fallback if API fails
        logger.warning("Using fallback document generation")
        return self._create_fallback_document(template_type, project_data, selected_companies)
    
    def _call_api(self, prompt, attempt=1):
        """Call the Mistral API with retry logic"""
        try:
            logger.info(f"API call attempt {attempt}/{self.max_retries}")
            
            headers = {
                "Content-Type": "application/json",
                "knowledge-project-apikey": self.api_key
            }
            
            data = {
                "text": prompt,
                "projectId": self.agent_id
            }
            
            response = requests.post(
                self.api_url, 
                headers=headers, 
                json=data,
                timeout=60  # Increase timeout for longer documents
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("answer", "")
                
                if answer and len(answer.strip()) > 10:
                    return answer
                else:
                    logger.warning(f"API returned empty or very short response: {answer[:50]}")
            else:
                logger.error(f"API error: Status {response.status_code}, {response.text[:100]}")
            
            # Retry if not successful and attempts remain
            if attempt < self.max_retries:
                logger.info(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
                return self._call_api(prompt, attempt + 1)
            
            return None
            
        except Exception as e:
            logger.error(f"API call error: {e}")
            
            # Retry if attempts remain
            if attempt < self.max_retries:
                logger.info(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
                return self._call_api(prompt, attempt + 1)
            
            return None
    
    def _create_analysis_prompt(self, document_text):
        """Create prompt for document analysis"""
        # Limit text length to avoid token limits
        max_chars = 6000
        text_sample = document_text[:max_chars] if len(document_text) > max_chars else document_text
        
        return f"""Analysez ce cahier des charges EDF pour un projet de moins de 400K€ et extrayez UNIQUEMENT les informations suivantes au format JSON.

DOCUMENT À ANALYSER:
{text_sample}

INSTRUCTIONS:
1. Identifiez les mots-clés principaux du projet (5-10 mots)
2. Identifiez les critères de sélection pertinents pour les entreprises
3. Identifiez les critères d'attribution et leur pondération (total = 100%)

Répondez UNIQUEMENT avec le format JSON suivant:
{{
    "keywords": ["mot1", "mot2", "mot3", "mot4", "mot5"],
    "selectionCriteria": [
        {{
            "id": 1,
            "name": "Nom du critère",
            "description": "Description détaillée du critère",
            "selected": true
        }},
        {{
            "id": 2,
            "name": "Autre critère",
            "description": "Description détaillée",
            "selected": true
        }}
    ],
    "attributionCriteria": [
        {{
            "id": 1,
            "name": "Prix",
            "weight": 40
        }},
        {{
            "id": 2,
            "name": "Valeur technique",
            "weight": 35
        }},
        {{
            "id": 3,
            "name": "Délai",
            "weight": 25
        }}
    ]
}}

Le JSON doit être valide et complet.
"""

    def _parse_analysis_response(self, response):
        """Parse and validate API response for document analysis"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_content = json_match.group(1)
            else:
                # Try to find JSON without markdown code blocks
                json_match = re.search(r'({.*})', response, re.DOTALL)
                if json_match:
                    json_content = json_match.group(1)
                else:
                    json_content = response
            
            # Parse JSON
            result = json.loads(json_content)
            
            # Validate structure
            if not isinstance(result, dict):
                raise ValueError("Response is not a valid JSON object")
            
            # Ensure required fields
            if "keywords" not in result or not isinstance(result["keywords"], list):
                result["keywords"] = ["EDF", "Projet", "Consultation"]
            
            if "selectionCriteria" not in result or not isinstance(result["selectionCriteria"], list):
                result["selectionCriteria"] = []
            
            if "attributionCriteria" not in result or not isinstance(result["attributionCriteria"], list):
                result["attributionCriteria"] = []
            
            # Validate and fix selection criteria
            for i, criterion in enumerate(result["selectionCriteria"]):
                if not isinstance(criterion, dict):
                    continue
                if "id" not in criterion:
                    criterion["id"] = i + 1
                if "name" not in criterion:
                    criterion["name"] = f"Critère {i + 1}"
                if "description" not in criterion:
                    criterion["description"] = "Description à compléter"
                if "selected" not in criterion:
                    criterion["selected"] = True
            
# Validate and fix attribution criteria
            total_weight = sum(criterion.get("weight", 0) for criterion in result["attributionCriteria"])
            
            if total_weight != 100 and result["attributionCriteria"]:
                # Adjust weights to total 100%
                if total_weight > 0:
                    factor = 100 / total_weight
                    for criterion in result["attributionCriteria"]:
                        criterion["weight"] = round(criterion["weight"] * factor)
                
                # Final adjustment to ensure total is exactly 100%
                current_total = sum(criterion["weight"] for criterion in result["attributionCriteria"])
                if current_total != 100 and result["attributionCriteria"]:
                    result["attributionCriteria"][0]["weight"] += (100 - current_total)
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error validating analysis response: {e}")
            return None
    
    def _create_fallback_analysis(self, document_text=None):
        """Create fallback analysis when API fails"""
        logger.info("Creating fallback analysis")
        
        # Extract keywords if document text is provided
        keywords = self._extract_keywords_from_text(document_text) if document_text else [
            "EDF", "Projet", "Maintenance", "Consultation", "Technique"
        ]
        
        # Default selection criteria
        selection_criteria = [
            {
                "id": 1,
                "name": "Certification MASE",
                "description": "L'entreprise doit être certifiée MASE pour intervenir sur sites EDF",
                "selected": True
            },
            {
                "id": 2,
                "name": "Expérience similaire",
                "description": "L'entreprise doit justifier d'expériences sur des projets similaires",
                "selected": True
            },
            {
                "id": 3,
                "name": "Zone d'intervention",
                "description": "L'entreprise doit pouvoir intervenir dans la zone géographique du projet",
                "selected": True
            },
            {
                "id": 4,
                "name": "Capacité technique",
                "description": "L'entreprise doit disposer des moyens techniques nécessaires",
                "selected": True
            }
        ]
        
        # Extract domain-specific criteria if document text is provided
        if document_text:
            domain_criteria = self._extract_domain_criteria(document_text)
            if domain_criteria:
                selection_criteria.append({
                    "id": 5,
                    "name": f"Compétence {domain_criteria}",
                    "description": f"L'entreprise doit avoir une expertise en {domain_criteria}",
                    "selected": True
                })
        
        # Default attribution criteria
        attribution_criteria = [
            {
                "id": 1,
                "name": "Prix",
                "weight": 40
            },
            {
                "id": 2,
                "name": "Valeur technique",
                "weight": 40
            },
            {
                "id": 3,
                "name": "Délai d'exécution",
                "weight": 20
            }
        ]
        
        return {
            "keywords": keywords,
            "selectionCriteria": selection_criteria,
            "attributionCriteria": attribution_criteria
        }
    
    def _extract_keywords_from_text(self, text):
        """Extract relevant keywords from document text"""
        if not text:
            return ["EDF", "Projet", "Consultation"]
        
        # Common technical terms to look for
        technical_terms = {
            "électricité": ["électr", "électriq", "courant", "tension", "aliment", "câbl"],
            "mécanique": ["mécan", "usinage", "tourna", "fraisage", "pièce"],
            "hydraulique": ["hydraul", "fluid", "eau", "circuit", "pompe", "écoulement"],
            "maintenance": ["mainten", "entretien", "réparation", "service", "dépannage"],
            "bâtiment": ["bâtiment", "construction", "génie civil", "maçonnerie"],
            "échangeur": ["échangeur", "plaque", "thermique", "chaleur", "transfert"],
            "nettoyage": ["nettoy", "décontam", "lavage", "décapage", "propreté"],
            "sécurité": ["sécurité", "prévention", "risque", "danger", "protection"]
        }
        
        # Lowercase text for matching
        text_lower = text.lower()
        
        # Find matching technical terms
        keywords = ["EDF", "Projet"]
        
        for term, patterns in technical_terms.items():
            if any(pattern in text_lower for pattern in patterns):
                keywords.append(term.capitalize())
        
        # Find location if mentioned
        locations = ["Chooz", "Ardennes", "Grand Est", "Nord-Est"]
        for location in locations:
            if location.lower() in text_lower:
                keywords.append(location)
                break
        
        # Add some general terms if needed
        if len(keywords) < 5:
            general_terms = ["Consultation", "Prestation", "Technique", "Industriel"]
            for term in general_terms:
                if term not in keywords and len(keywords) < 8:
                    keywords.append(term)
        
        return keywords[:10]  # Limit to 10 keywords
    
    def _extract_domain_criteria(self, text):
        """Extract domain-specific criteria from document text"""
        text_lower = text.lower()
        
        # Domain detection
        domains = {
            "électricité": ["électr", "électriq", "courant", "tension", "aliment", "câbl"],
            "mécanique": ["mécan", "usinage", "tourna", "fraisage", "pièce"],
            "hydraulique": ["hydraul", "fluid", "eau", "circuit", "pompe", "écoulement"],
            "échangeur thermique": ["échangeur", "plaque", "thermique", "chaleur"],
            "nettoyage industriel": ["nettoy", "décontam", "lavage", "décapage"],
            "maintenance": ["mainten", "entretien", "réparation", "service"]
        }
        
        for domain, patterns in domains.items():
            if any(pattern in text_lower for pattern in patterns):
                return domain
        
        return None
    
    def _create_document_prompt(self, template_type, project_data, selected_companies=None):
        """Create prompt for document generation"""
        # Document type descriptions
        doc_descriptions = {
            "projetMarche": "un projet de marché (clauses administratives et techniques)",
            "reglementConsultation": "un règlement de consultation",
            "lettreConsultation": "une lettre de consultation",
            "grilleEvaluation": "une grille d'évaluation avec les critères d'attribution"
        }
        
        doc_type = doc_descriptions.get(template_type, "un document de consultation")
        
        # Project information
        project_title = project_data.get('title', 'Projet EDF')
        project_description = project_data.get('description', '')
        
        # Selection criteria
        selection_criteria = project_data.get('selectionCriteria', [])
        selection_criteria_text = ""
        if selection_criteria:
            selection_criteria_text = "Critères de sélection:\n"
            for criterion in selection_criteria:
                if criterion.get('selected', False):
                    selection_criteria_text += f"- {criterion.get('name')}: {criterion.get('description', '')}\n"
        
        # Attribution criteria
        attribution_criteria = project_data.get('attributionCriteria', [])
        attribution_criteria_text = ""
        if attribution_criteria:
            attribution_criteria_text = "Critères d'attribution:\n"
            for criterion in attribution_criteria:
                attribution_criteria_text += f"- {criterion.get('name')}: {criterion.get('weight')}%\n"
        
        # Selected companies
        companies_text = ""
        if selected_companies:
            companies_text = "Entreprises consultées:\n"
            for company in selected_companies:
                if company.get('selected', True):
                    companies_text += f"- {company.get('name')} ({company.get('location', 'N/A')})\n"
        
        # Build prompt
        prompt = f"""Générez {doc_type} professionnel pour EDF.

PROJET: {project_title}
DESCRIPTION: {project_description}

{selection_criteria_text}
{attribution_criteria_text}
{companies_text}

Le document doit être structuré, professionnel et conforme aux standards EDF.
Répondez uniquement avec le contenu du document sans autre commentaire ou code.
"""
        
        return prompt
    
    def _format_document_content(self, content, template_type):
        """Format and clean the document content"""
        # Remove any markdown code blocks
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        
        # Remove any explanatory text before or after the document
        content = re.sub(r'^.*?Voici (le|la) (document|lettre|règlement|grille).*?\n', '', content, flags=re.DOTALL)
        content = re.sub(r'\n.*?(J\'espère que ce document|N\'hésitez pas à).*?$', '', content, flags=re.DOTALL)
        
        # Final cleanup
        content = content.strip()
        
        return content
    
    def _create_fallback_document(self, template_type, project_data, selected_companies=None):
        """Create fallback document when API fails"""
        logger.info(f"Creating fallback document for {template_type}")
        
        project_title = project_data.get('title', 'Projet EDF')
        project_description = project_data.get('description', 'Description du projet')
        
        # Get today's date
        today = datetime.now().strftime("%d/%m/%Y")
        
        # Templates for different document types
        templates = {
            "projetMarche": f"""PROJET DE MARCHÉ

Objet: {project_title}
Date: {today}

1. DISPOSITIONS GÉNÉRALES

1.1 Objet du marché
Le présent marché a pour objet : {project_description}

1.2 Documents contractuels
Le marché est constitué des documents énumérés ci-dessous:
- Le présent projet de marché
- Le cahier des charges techniques
- Les conditions générales d'achat EDF

2. CONDITIONS D'EXÉCUTION

2.1 Délai d'exécution
Le délai d'exécution est fixé à [délai] à compter de la notification du marché.

2.2 Conditions techniques
Les prestations seront exécutées conformément aux règles de l'art et aux normes en vigueur.

3. CLAUSES FINANCIÈRES

3.1 Prix
Les prix sont fermes et non révisables pendant la durée du marché.

3.2 Modalités de paiement
Les paiements seront effectués par virement bancaire dans un délai de 60 jours à compter de la réception de la facture.

4. DISPOSITIONS DIVERSES

4.1 Confidentialité
Le titulaire s'engage à respecter la confidentialité des informations communiquées par EDF.

4.2 Résiliation
EDF peut résilier le marché en cas de manquement du titulaire à ses obligations contractuelles.
""",

            "reglementConsultation": f"""RÈGLEMENT DE CONSULTATION

Objet: {project_title}
Date: {today}

1. OBJET DE LA CONSULTATION
La présente consultation concerne : {project_description}

2. CONDITIONS DE LA CONSULTATION

2.1 Procédure
La présente consultation est lancée selon une procédure adaptée.

2.2 Délai de validité des offres
Le délai de validité des offres est fixé à 90 jours à compter de la date limite de remise des offres.

3. PRÉSENTATION DES OFFRES

3.1 Documents à produire
Les candidats devront produire les documents suivants:
- Lettre de candidature
- Déclaration sur l'honneur
- Références sur des prestations similaires
- Moyens techniques et humains
- Certifications et qualifications
- Mémoire technique
- Proposition financière

4. CRITÈRES D'ATTRIBUTION

Les offres seront jugées selon les critères suivants:
{"".join([f"- {c.get('name')}: {c.get('weight')}%\n" for c in project_data.get('attributionCriteria', [])])}

5. CONDITIONS D'ENVOI DES OFFRES

Les offres devront être transmises par voie électronique à l'adresse suivante:
[adresse email]

Date limite de réception des offres: [date]
""",

            "lettreConsultation": f"""
Objet : Consultation pour {project_title}

Madame, Monsieur,

Dans le cadre de nos activités, EDF souhaite lancer une consultation pour:
{project_description}

Nous vous invitons à présenter une offre pour cette prestation.

Vous trouverez en pièces jointes:
- Le cahier des charges techniques
- Le règlement de consultation
- Le projet de marché

Votre offre devra comprendre:
- Un mémoire technique détaillant votre proposition
- Les références de prestations similaires
- Les certifications et qualifications pertinentes
- Une proposition financière détaillée

Les critères d'attribution sont les suivants:
{"".join([f"- {c.get('name')}: {c.get('weight')}%\n" for c in project_data.get('attributionCriteria', [])])}

La date limite de remise des offres est fixée au [date].

Nous vous remercions de l'attention que vous porterez à notre demande et restons à votre disposition pour tout complément d'information.

Veuillez agréer, Madame, Monsieur, l'expression de nos salutations distinguées.

[Responsable Achats]
EDF
""",

            "grilleEvaluation": f"""GRILLE D'ÉVALUATION

Projet: {project_title}
Date: {today}

CRITÈRES D'ÉVALUATION

{"".join([f"{i+1}. {c.get('name')} ({c.get('weight')}%)\n" for i, c in enumerate(project_data.get('attributionCriteria', []))])}

TABLEAU D'ÉVALUATION

Entreprises:
{"".join([f"- {c.get('name')} ({c.get('location', 'N/A')})\n" for c in selected_companies or []])}

Barème de notation:
- 0/5 : Très insuffisant
- 1/5 : Insuffisant
- 2/5 : Moyen
- 3/5 : Satisfaisant
- 4/5 : Très satisfaisant
- 5/5 : Excellent

[Tableau d'évaluation à compléter]
"""
        }
        
        return templates.get(template_type, f"Document {template_type} pour {project_title}")

def analyze_document(document_text, api_key, agent_id=None):
    """
    Analyze a document to extract criteria
    
    Args:
        document_text: Text content of the document
        api_key: Mistral API key
        agent_id: Mistral agent ID (optional)
        
    Returns:
        Dictionary with keywords, selection criteria, and attribution criteria
    """
    mistral = MistralAPI(api_key, agent_id)
    return mistral.analyze_document(document_text)

def generate_document(template_type, project_data, api_key, agent_id=None):
    """
    Generate a document based on template type and project data
    
    Args:
        template_type: Type of document to generate
        project_data: Dictionary with project information
        api_key: Mistral API key
        agent_id: Mistral agent ID (optional)
        
    Returns:
        Generated document content
    """
    mistral = MistralAPI(api_key, agent_id)
    selected_companies = project_data.get('companies', [])
    return mistral.generate_document(template_type, project_data, selected_companies)

def get_agent_answer(question, api_key, agent_id):
    """
    Get a direct answer from the Mistral agent
    
    Args:
        question: Question to ask
        api_key: Mistral API key
        agent_id: Mistral agent ID
        
    Returns:
        Agent's answer as text
    """
    mistral = MistralAPI(api_key, agent_id)
    return mistral._call_api(question) or "Je ne peux pas répondre à cette question pour le moment."