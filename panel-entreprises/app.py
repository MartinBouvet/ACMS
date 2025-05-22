from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import pandas as pd
from werkzeug.utils import secure_filename
import traceback
from datetime import datetime
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import des utilitaires
from utils.excel_parser import load_companies_from_excel
from utils.mistral_api import analyze_document, generate_document, get_agent_answer
from utils.company_matcher import match_companies
from utils.document_generator import create_document

# Configuration Flask
app = Flask(__name__)
CORS(app)

# Configuration des chemins
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GENERATED_DOCS'] = 'generated'
app.config['TEMPLATE_DOCS'] = 'templates_docs'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Configuration API Prisme AI
app.config['PRISME_API_KEY'] = 'cec930ebb79846da94d2cf5028177995'
app.config['PRISME_AGENT_ID'] = '67f785d59e82260f684a217a'

# Créer les dossiers nécessaires
for folder in [app.config['UPLOAD_FOLDER'], app.config['GENERATED_DOCS'], 
               app.config['TEMPLATE_DOCS'], 'data']:
    os.makedirs(folder, exist_ok=True)

def find_excel_file():
    """Trouve automatiquement le fichier Excel des entreprises"""
    logger.info("=== RECHERCHE FICHIER EXCEL ===")
    
    # Chemins possibles
    possible_paths = [
        'DACI GP_ORANO DS_Nettoyages des échangeurs à plaques_CNPE CHOOZ signé .xlsx',
        'data/DACI GP_ORANO DS_Nettoyages des échangeurs à plaques_CNPE CHOOZ signé .xlsx',
        'ACMS Publipostage FINAL V4.xlsx',
        'data/ACMS Publipostage FINAL V4.xlsx'
    ]
    
    # Chercher le fichier spécifique
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Fichier Excel trouvé: {path}")
            return path
    
    # Chercher tous les fichiers Excel
    logger.info("Recherche de fichiers Excel dans le répertoire...")
    
    excel_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(('.xlsx', '.xls')):
                full_path = os.path.join(root, file)
                excel_files.append(full_path)
                logger.info(f"Fichier Excel trouvé: {full_path}")
    
    # Prioriser les fichiers avec certains mots-clés
    priority_keywords = ['daci', 'orano', 'acms', 'publipostage', 'entreprise']
    
    for excel_file in excel_files:
        file_lower = excel_file.lower()
        if any(keyword in file_lower for keyword in priority_keywords):
            logger.info(f"Fichier Excel prioritaire sélectionné: {excel_file}")
            return excel_file
    
    # Prendre le premier fichier Excel trouvé
    if excel_files:
        logger.info(f"Premier fichier Excel utilisé: {excel_files[0]}")
        return excel_files[0]
    
    logger.warning("Aucun fichier Excel trouvé!")
    return None

def load_companies_safely():
    """Charge les entreprises avec gestion d'erreurs robuste"""
    try:
        excel_file = find_excel_file()
        
        if not excel_file:
            logger.warning("Aucun fichier Excel trouvé, création d'entreprises de test")
            return create_test_companies()
        
        logger.info(f"Chargement des entreprises depuis: {excel_file}")
        companies = load_companies_from_excel(excel_file)
        
        if not companies:
            logger.warning("Aucune entreprise extraite, création d'entreprises de test")
            return create_test_companies()
        
        logger.info(f"✅ {len(companies)} entreprises chargées avec succès")
        
        # Afficher un résumé des domaines
        domain_stats = {}
        for company in companies:
            domain = company.get('domain', 'Autre')
            domain_stats[domain] = domain_stats.get(domain, 0) + 1
        
        logger.info("Répartition par domaine:")
        for domain, count in domain_stats.items():
            logger.info(f"  - {domain}: {count}")
        
        return companies
        
    except Exception as e:
        logger.error(f"Erreur lors du chargement des entreprises: {e}")
        logger.error(traceback.format_exc())
        return create_test_companies()

def create_test_companies():
    """Crée des entreprises de test si aucun fichier Excel n'est disponible"""
    logger.info("Création d'entreprises de test...")
    
    test_companies = [
        {
            'id': 'ENT_001',
            'name': 'TECHNI-MAINTENANCE SAS',
            'location': 'Chooz, Ardennes (08)',
            'domain': 'Maintenance',
            'certifications': ['MASE', 'ISO 9001'],
            'ca': '2.5M€',
            'employees': '35',
            'contact': {'email': 'contact@techni-maintenance.fr', 'phone': '03.24.42.XX.XX'},
            'experience': 'Spécialisée dans la maintenance d\'échangeurs thermiques depuis 15 ans. Références sur centrales nucléaires.',
            'lots_marches': [
                {'type': 'Maintenance', 'description': 'Nettoyage échangeurs à plaques - CNPE Chooz (2022)'},
                {'type': 'Maintenance', 'description': 'Maintenance circuit primaire - CNPE Cattenom (2021)'}
            ],
            'score': 0
        },
        {
            'id': 'ENT_002',
            'name': 'HYDRAULIQUE SERVICES',
            'location': 'Charleville-Mézières, Ardennes (08)',
            'domain': 'Hydraulique',
            'certifications': ['MASE', 'ISO 14001', 'CEFRI'],
            'ca': '1.8M€',
            'employees': '28',
            'contact': {'email': 'direction@hydraulique-services.fr'},
            'experience': 'Expert en circuits hydrauliques industriels. Interventions régulières sur sites nucléaires.',
            'lots_marches': [
                {'type': 'Hydraulique', 'description': 'Rénovation circuit hydraulique - Site industriel (2023)'},
                {'type': 'Maintenance', 'description': 'Nettoyage tuyauteries - CNPE Chooz (2022)'}
            ],
            'score': 0
        },
        {
            'id': 'ENT_003',
            'name': 'ELECTRO-TECH GRAND EST',
            'location': 'Metz, Moselle (57)',
            'domain': 'Électricité',
            'certifications': ['MASE', 'ISO 9001', 'QUALIBAT'],
            'ca': '3.2M€',
            'employees': '45',
            'contact': {'email': 'contact@electro-tech-ge.fr', 'phone': '03.87.XX.XX.XX'},
            'experience': 'Installations électriques industrielles complexes. Habilitations nucléaires.',
            'lots_marches': [
                {'type': 'Électricité', 'description': 'Installation électrique - Site industriel Moselle (2023)'},
                {'type': 'Maintenance', 'description': 'Maintenance électrique - CNPE Cattenom (2022)'}
            ],
            'score': 0
        },
        {
            'id': 'ENT_004',
            'name': 'MECANIQUE PRECISION',
            'location': 'Reims, Marne (51)',
            'domain': 'Mécanique',
            'certifications': ['ISO 9001', 'ISO 14001'],
            'ca': '1.2M€',
            'employees': '22',
            'contact': {'email': 'info@mecanique-precision.fr'},
            'experience': 'Usinage de précision pour l\'industrie. Pièces pour équipements thermiques.',
            'lots_marches': [
                {'type': 'Mécanique', 'description': 'Fabrication pièces échangeurs - Industrie (2023)'}
            ],
            'score': 0
        },
        {
            'id': 'ENT_005',
            'name': 'BTP CONSTRUCTION EST',
            'location': 'Strasbourg, Bas-Rhin (67)',
            'domain': 'Bâtiment',
            'certifications': ['QUALIBAT', 'RGE'],
            'ca': '4.1M€',
            'employees': '58',
            'contact': {'email': 'commercial@btp-construction-est.fr'},
            'experience': 'Gros œuvre et second œuvre pour l\'industrie. Constructions spécialisées.',
            'lots_marches': [
                {'type': 'Bâtiment', 'description': 'Construction bâtiment technique - Site industriel (2023)'}
            ],
            'score': 0
        }
    ]
    
    logger.info(f"✅ {len(test_companies)} entreprises de test créées")
    return test_companies

# Charger les entreprises au démarrage
logger.info("=== DÉMARRAGE APPLICATION ===")
COMPANIES = load_companies_safely()
logger.info(f"Application démarrée avec {len(COMPANIES)} entreprises")

# Extensions de fichiers autorisées
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'xlsx', 'xls', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Historique des demandes (exemple)
ACTIVITIES = [
    {
        'icon': '📝',
        'title': 'Projet de nettoyage des échangeurs à plaques - CNPE Chooz',
        'timestamp': 'il y a 2 jours',
        'url': '/search'
    },
    {
        'icon': '👥',
        'title': 'Consultation maintenance circuit hydraulique',
        'timestamp': 'il y a 5 jours',
        'url': '/search'
    },
    {
        'icon': '📄',
        'title': 'Documents générés pour projet électrique',
        'timestamp': 'il y a 1 semaine',
        'url': '/documents'
    }
]

# ================================================
# ROUTES PRINCIPALES
# ================================================

@app.route('/')
def index():
    return render_template('pages/dashboard.html', page='dashboard', activities=ACTIVITIES)

@app.route('/dashboard')
def dashboard():
    return render_template('pages/dashboard.html', page='dashboard', activities=ACTIVITIES)

@app.route('/search')
def search():
    return render_template('pages/search.html', page='search')

@app.route('/database')
def database():
    logger.info(f"Page base de données - {len(COMPANIES)} entreprises")
    return render_template('pages/database.html', page='database', companies=COMPANIES)

@app.route('/guide')
def guide():
    return render_template('pages/guide.html', page='guide')

@app.route('/support')
def support():
    return render_template('pages/support.html', page='support')

@app.route('/documents')
def documents():
    template_docs = []
    try:
        if os.path.exists(app.config['TEMPLATE_DOCS']):
            for filename in os.listdir(app.config['TEMPLATE_DOCS']):
                if filename.startswith('.'):
                    continue
                    
                file_path = os.path.join(app.config['TEMPLATE_DOCS'], filename)
                if os.path.isfile(file_path):
                    doc_type = determine_document_type(filename)
                    mod_time = os.path.getmtime(file_path)
                    mod_date = datetime.fromtimestamp(mod_time).strftime('%d/%m/%Y')
                    
                    template_docs.append({
                        'id': f"doc_{len(template_docs) + 1}",
                        'name': filename.split('.')[0],
                        'fileName': filename,
                        'type': doc_type,
                        'date': mod_date,
                        'url': f"/api/documents/template/download/{filename}"
                    })
    except Exception as e:
        logger.error(f"Erreur chargement documents types: {e}")
    
    return render_template('pages/documents.html', page='documents', documents=template_docs)

def determine_document_type(filename):
    """Détermine le type de document basé sur le nom de fichier"""
    filename_lower = filename.lower()
    
    if any(word in filename_lower for word in ['reglement', 'règlement']):
        return 'reglement'
    elif any(word in filename_lower for word in ['marche', 'marché', 'cpa']):
        return 'marche'
    elif any(word in filename_lower for word in ['lettre']):
        return 'lettre'
    elif any(word in filename_lower for word in ['grille', 'evalua']):
        return 'grille'
    else:
        return 'autre'

# ================================================
# ROUTES API
# ================================================

@app.route('/api/companies', methods=['GET'])
def get_all_companies():
    """Retourne toutes les entreprises"""
    try:
        logger.info(f"API /api/companies - Retour de {len(COMPANIES)} entreprises")
        return jsonify({"success": True, "data": COMPANIES})
    except Exception as e:
        logger.error(f"Erreur API companies: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/files/parse-document', methods=['POST'])
def parse_document():
    """Parse un document uploadé"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "Aucun fichier fourni"}), 400
            
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"success": False, "message": "Aucun fichier sélectionné"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"success": False, "message": "Type de fichier non autorisé"}), 400
        
        # Sauvegarder le fichier
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        logger.info(f"Fichier sauvé: {file_path}")
        
        # Extraire le texte selon le type de fichier
        text = extract_text_from_file(file_path, filename)
        
        return jsonify({
            "success": True,
            "data": {
                "fileName": filename,
                "mimeType": file.mimetype,
                "text": text
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur parse document: {e}")
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500

def extract_text_from_file(file_path, filename):
    """Extrait le texte d'un fichier selon son type"""
    try:
        if filename.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif filename.endswith('.pdf'):
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text
            except ImportError:
                return f"[Contenu PDF - {filename}] Module PyPDF2 non disponible"
        
        elif filename.endswith(('.docx', '.doc')):
            try:
                from docx import Document
                doc = Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs])
                return text
            except ImportError:
                return f"[Contenu DOCX - {filename}] Module python-docx non disponible"
        
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
            return df.to_string()
        
        else:
            return f"[Fichier {filename}] - Type non supporté pour extraction de texte"
            
    except Exception as e:
        logger.error(f"Erreur extraction texte: {e}")
        return f"[Erreur extraction texte du fichier {filename}]"

@app.route('/api/ia/analyze-document', methods=['POST'])
def api_analyze_document():
    """Analyse un document avec l'IA"""
    try:
        data = request.json
        document_text = data.get('documentText', '')
        
        logger.info(f"=== ANALYSE DOCUMENT ===")
        logger.info(f"Longueur texte: {len(document_text)} caractères")
        
        if not document_text:
            return jsonify({"success": False, "message": "Texte du document requis"}), 400
        
        # Analyser avec l'API Mistral
        analysis_results = analyze_document(document_text, app.config['PRISME_API_KEY'])
        
        logger.info(f"Analyse terminée: {len(analysis_results.get('keywords', []))} mots-clés")
        
        return jsonify({"success": True, "data": analysis_results})
        
    except Exception as e:
        logger.error(f"Erreur analyse document: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ia/find-matching-companies', methods=['POST'])
def api_find_matching_companies():
    """Trouve les entreprises correspondant aux critères"""
    try:
        data = request.json
        criteria = data.get('criteria', [])
        
        logger.info(f"=== MATCHING ENTREPRISES ===")
        logger.info(f"Critères reçus: {len(criteria)}")
        logger.info(f"Entreprises disponibles: {len(COMPANIES)}")
        
        if not criteria:
            return jsonify({"success": False, "message": "Critères requis"}), 400
        
        if not COMPANIES:
            return jsonify({"success": False, "message": "Aucune entreprise en base"}), 400
        
        # Utiliser l'algorithme de matching amélioré
        matched_companies = match_companies(COMPANIES, criteria)
        
        logger.info(f"Matching terminé: {len(matched_companies)} entreprises")
        if matched_companies:
            logger.info(f"Meilleur match: {matched_companies[0]['name']} ({matched_companies[0]['score']}%)")
        
        return jsonify({"success": True, "data": matched_companies})
        
    except Exception as e:
        logger.error(f"Erreur matching: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/documents/generate', methods=['POST'])
def api_generate_document():
    """Génère un document de consultation"""
    try:
        data = request.json
        template_type = data.get('templateType')
        project_data = data.get('projectData', {})
        companies = data.get('companies', [])
        
        logger.info(f"Génération document: {template_type}")
        
        if not template_type:
            return jsonify({"success": False, "message": "Type de document requis"}), 400
        
        # Générer le document
        document_content = generate_document(
            template_type, 
            project_data, 
            app.config['PRISME_API_KEY']
        )
        
        # Sauvegarder le document
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        project_id = project_data.get('id', 'projet').replace(' ', '_')
        
        extension = 'xlsx' if template_type == 'grilleEvaluation' else 'txt'
        
        prefix_map = {
            'projetMarche': 'PM',
            'reglementConsultation': 'RC',
            'grilleEvaluation': 'GE',
            'lettreConsultation': 'LC'
        }
        prefix = prefix_map.get(template_type, 'DOC')
        
        filename = f"{prefix}_{project_id}_{timestamp}.{extension}"
        file_path = os.path.join(app.config['GENERATED_DOCS'], filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(document_content)
        
        logger.info(f"Document généré: {filename}")
        
        return jsonify({
            "success": True,
            "data": {
                "fileName": filename,
                "fileUrl": f"/api/documents/download/{filename}",
                "type": extension
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur génération document: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ================================================
# ROUTES DE TÉLÉCHARGEMENT
# ================================================

@app.route('/api/documents/download/<filename>')
def download_document(filename):
    """Télécharge un document généré"""
    return send_from_directory(app.config['GENERATED_DOCS'], filename)

@app.route('/api/documents/template/download/<filename>')
def download_template_document(filename):
    """Télécharge un document template"""
    return send_from_directory(app.config['TEMPLATE_DOCS'], filename)

@app.route('/api/files/download/<filename>')
def download_file(filename):
    """Télécharge un fichier uploadé"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ================================================
# ROUTES BASE DE DONNÉES
# ================================================

@app.route('/api/database/import-excel', methods=['POST'])
def import_excel():
    """Importe des entreprises depuis Excel"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "Aucun fichier fourni"}), 400
            
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"success": False, "message": "Aucun fichier sélectionné"}), 400
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({"success": False, "message": "Format Excel requis"}), 400
        
        # Sauvegarder temporairement
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{filename}")
        file.save(temp_path)
        
        logger.info(f"Import Excel: {temp_path}")
        
        # Charger les nouvelles entreprises
        new_companies = load_companies_from_excel(temp_path)
        
        # Supprimer le fichier temporaire
        os.remove(temp_path)
        
        if new_companies:
            global COMPANIES
            # Fusionner sans doublons
            existing_names = {comp['name'].lower() for comp in COMPANIES}
            added_count = 0
            
            for company in new_companies:
                if company['name'].lower() not in existing_names:
                    COMPANIES.append(company)
                    added_count += 1
            
            logger.info(f"Import réussi: {added_count} nouvelles entreprises")
            
            return jsonify({
                "success": True, 
                "message": f"{added_count} nouvelles entreprises importées",
                "imported": added_count,
                "total": len(new_companies)
            })
        else:
            return jsonify({"success": False, "message": "Aucune entreprise trouvée"}), 400
            
    except Exception as e:
        logger.error(f"Erreur import Excel: {e}")
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500

@app.route('/api/database/add-company', methods=['POST'])
def add_company():
    """Ajoute une nouvelle entreprise"""
    try:
        data = request.json
        company_name = data.get('name')
        
        if not company_name:
            return jsonify({"success": False, "message": "Nom requis"}), 400
        
        # Créer nouvelle entreprise
        company_id = f"ENT_{str(len(COMPANIES) + 1).zfill(3)}"
        
        new_company = {
            'id': company_id,
            'name': company_name,
            'domain': data.get('domain', 'Autre'),
            'location': data.get('location', 'Non spécifié'),
            'certifications': data.get('certifications', []),
            'ca': data.get('ca', 'Non spécifié'),
            'employees': data.get('employees', 'Non spécifié'),
            'contact': data.get('contact', {}),
            'experience': data.get('experience', 'Non spécifié'),
            'lots_marches': [],
            'score': 0
        }
        
        COMPANIES.append(new_company)
        
        logger.info(f"Entreprise ajoutée: {company_name}")
        
        return jsonify({"success": True, "data": new_company})
        
    except Exception as e:
        logger.error(f"Erreur ajout entreprise: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/database/update-company', methods=['POST'])
def update_company():
    """Met à jour une entreprise"""
    try:
        data = request.json
        company_id = data.get('id')
        
        if not company_id:
            return jsonify({"success": False, "message": "ID requis"}), 400
        
        # Trouver et mettre à jour l'entreprise
        for i, company in enumerate(COMPANIES):
            if company['id'] == company_id:
                for key, value in data.items():
                    if key != 'id':
                        COMPANIES[i][key] = value
                
                logger.info(f"Entreprise mise à jour: {COMPANIES[i]['name']}")
                return jsonify({"success": True, "data": COMPANIES[i]})
        
        return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404
        
    except Exception as e:
        logger.error(f"Erreur mise à jour: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/database/delete-company', methods=['DELETE'])
def delete_company():
    """Supprime une entreprise"""
    try:
        data = request.json
        company_id = data.get('id')
        
        if not company_id:
            return jsonify({"success": False, "message": "ID requis"}), 400
        
        global COMPANIES
        original_count = len(COMPANIES)
        COMPANIES = [company for company in COMPANIES if company['id'] != company_id]
        
        if len(COMPANIES) < original_count:
            logger.info(f"Entreprise supprimée: {company_id}")
            return jsonify({"success": True, "message": "Entreprise supprimée"})
        else:
            return jsonify({"success": False, "message": "Entreprise non trouvée"}), 404
            
    except Exception as e:
        logger.error(f"Erreur suppression: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

# ================================================
# GESTIONNAIRE D'ERREURS
# ================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Ressource non trouvée"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Erreur interne: {error}")
    return jsonify({"success": False, "error": "Erreur interne du serveur"}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({"success": False, "error": "Fichier trop volumineux"}), 413

# ================================================
# DÉMARRAGE DE L'APPLICATION
# ================================================

if __name__ == '__main__':
    logger.info("=== DÉMARRAGE DU SERVEUR ===")
    logger.info(f"Entreprises chargées: {len(COMPANIES)}")
    logger.info("Serveur disponible sur: http://localhost:5001")
    logger.info("=== PRÊT ===")
    
    app.run(debug=True, host='0.0.0.0', port=5001)