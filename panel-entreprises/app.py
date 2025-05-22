from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
import os
import json
import pandas as pd
from werkzeug.utils import secure_filename
import traceback
from datetime import datetime

# Import des utilitaires
from utils.excel_parser import load_companies_from_excel
from utils.mistral_api import analyze_document, generate_document, get_agent_answer
from utils.company_matcher import match_companies
from utils.document_generator import create_document

# Configuration
app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GENERATED_DOCS'] = 'generated'
app.config['TEMPLATE_DOCS'] = 'templates_docs'  # Dossier pour les documents types
app.config['COMPANIES_EXCEL'] = 'DACI GP_ORANO DS_Nettoyages des échangeurs à plaques_CNPE CHOOZ signé .xlsx'
app.config['PRISME_API_KEY'] = 'cec930ebb79846da94d2cf5028177995'
app.config['PRISME_AGENT_ID'] = '67f785d59e82260f684a217a'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

# Créer les dossiers nécessaires
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_DOCS'], exist_ok=True)
os.makedirs(app.config['TEMPLATE_DOCS'], exist_ok=True)
os.makedirs('data', exist_ok=True)

def debug_excel_loading():
    """Debug le chargement du fichier Excel"""
    print("=== DEBUG CHARGEMENT EXCEL ===")
    
    # Vérifier les fichiers présents
    current_dir = os.getcwd()
    print(f"Répertoire courant: {current_dir}")
    
    # Lister les fichiers Excel dans le répertoire courant
    excel_files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls'))]
    print(f"Fichiers Excel trouvés dans la racine: {excel_files}")
    
    # Vérifier aussi dans le dossier data
    data_dir = 'data'
    if os.path.exists(data_dir):
        data_excel_files = [f for f in os.listdir(data_dir) if f.endswith(('.xlsx', '.xls'))]
        print(f"Fichiers Excel trouvés dans /data: {data_excel_files}")
        excel_files.extend([os.path.join(data_dir, f) for f in data_excel_files])
    
    # Vérifier le fichier spécifique
    excel_file = app.config['COMPANIES_EXCEL']
    print(f"Fichier configuré: {excel_file}")
    print(f"Fichier existe: {os.path.exists(excel_file)}")
    
    if os.path.exists(excel_file):
        print(f"Taille du fichier: {os.path.getsize(excel_file)} bytes")
    
    return excel_files

# Charger les entreprises à partir du fichier Excel avec debug
COMPANIES = []
try:
    # Debug du fichier Excel
    excel_files = debug_excel_loading()
    
    # Si le fichier configuré n'existe pas, essayer de le trouver
    excel_file = app.config['COMPANIES_EXCEL']
    if not os.path.exists(excel_file):
        print(f"Fichier {excel_file} non trouvé, recherche automatique...")
        
        # Chercher un fichier Excel contenant "DACI" ou "ORANO"
        for filename in excel_files:
            base_filename = os.path.basename(filename)
            if any(keyword in base_filename.upper() for keyword in ['DACI', 'ORANO', 'ACMS', 'PUBLIPOSTAGE']):
                excel_file = filename
                app.config['COMPANIES_EXCEL'] = excel_file
                print(f"Utilisation du fichier trouvé: {excel_file}")
                break
    
    if os.path.exists(excel_file):
        print(f"Chargement du fichier: {excel_file}")
        COMPANIES = load_companies_from_excel(excel_file)
        print(f"Chargé {len(COMPANIES)} entreprises depuis le fichier Excel")
        
        # Afficher quelques exemples
        if COMPANIES:
            print("=== EXEMPLES D'ENTREPRISES CHARGÉES ===")
            for i, company in enumerate(COMPANIES[:5]):
                print(f"Entreprise {i+1}:")
                print(f"  - ID: {company.get('id', 'N/A')}")
                print(f"  - Nom: {company.get('name', 'N/A')}")
                print(f"  - Domaine: {company.get('domain', 'N/A')}")
                print(f"  - Localisation: {company.get('location', 'N/A')}")
                print(f"  - Certifications: {company.get('certifications', [])}")
                print(f"  - CA: {company.get('ca', 'N/A')}")
                print(f"  - Effectifs: {company.get('employees', 'N/A')}")
                print()
        else:
            print("ATTENTION: Aucune entreprise n'a été extraite du fichier Excel!")
    else:
        print(f"ERREUR: Aucun fichier Excel trouvé !")
        print("Fichiers Excel disponibles:", excel_files)
        print("Vérifiez que votre fichier Excel est bien présent dans le répertoire du projet.")
        
except Exception as e:
    print(f"Erreur lors du chargement du fichier Excel: {e}")
    print(traceback.format_exc())
    print("=== INFORMATIONS DE DEBUG ===")
    print(f"Répertoire de travail: {os.getcwd()}")
    print(f"Fichiers dans le répertoire: {os.listdir('.')}")

# Extensions autorisées pour les fichiers
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'xlsx', 'xls', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Définir l'historique des demandes statique pour la démonstration
ACTIVITIES = [
    {
        'icon': '📝',
        'title': 'Projet de rénovation des échangeurs à plaques',
        'timestamp': 'il y a 2 jours',
        'url': '/search'
    },
    {
        'icon': '👥',
        'title': 'Consultation lancée pour le projet de maintenance',
        'timestamp': 'il y a 5 jours',
        'url': '/search'
    },
    {
        'icon': '📄',
        'title': 'Documents générés pour le projet hydraulique',
        'timestamp': 'il y a 1 semaine',
        'url': '/documents'
    }
]

# Routes pour les pages web
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
    print(f"Route /database appelée - Nombre d'entreprises: {len(COMPANIES)}")
    if COMPANIES:
        print(f"Première entreprise: {COMPANIES[0]}")
    return render_template('pages/database.html', page='database', companies=COMPANIES)

@app.route('/guide')
def guide():
    return render_template('pages/guide.html', page='guide')

@app.route('/support')
def support():
    return render_template('pages/support.html', page='support')

@app.route('/documents')
def documents():
    # Récupérer la liste des documents types
    template_docs = []
    try:
        if os.path.exists(app.config['TEMPLATE_DOCS']):
            for filename in os.listdir(app.config['TEMPLATE_DOCS']):
                file_path = os.path.join(app.config['TEMPLATE_DOCS'], filename)
                if os.path.isfile(file_path) and not filename.startswith('.'):
                    # Déterminer le type de document
                    doc_type = 'autre'
                    if 'reglement' in filename.lower():
                        doc_type = 'reglement'
                    elif 'marche' in filename.lower() or 'cpa' in filename.lower():
                        doc_type = 'marche'
                    elif 'lettre' in filename.lower():
                        doc_type = 'lettre'
                    elif 'grille' in filename.lower() or 'evalua' in filename.lower():
                        doc_type = 'grille'
                    
                    # Obtenir la date de modification
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
        print(f"Erreur lors de la récupération des documents types: {e}")
    
    return render_template('pages/documents.html', page='documents', documents=template_docs)

# Routes API
@app.route('/api/companies', methods=['GET'])
def get_all_companies():
    try:
        print(f"API /api/companies appelée - Retour de {len(COMPANIES)} entreprises")
        return jsonify({"success": True, "data": COMPANIES})
    except Exception as e:
        print(f"Erreur dans /api/companies: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/files/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Aucun fichier fourni"})
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"success": False, "message": "Aucun fichier sélectionné"})
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        return jsonify({
            "success": True,
            "message": "Fichier téléversé avec succès",
            "data": {
                "originalName": file.filename,
                "fileName": filename,
                "path": file_path,
                "url": f"/api/files/download/{filename}"
            }
        })
    
    return jsonify({"success": False, "message": "Type de fichier non autorisé"})

@app.route('/api/files/parse-document', methods=['POST'])
def parse_document():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Aucun fichier fourni"})
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"success": False, "message": "Aucun fichier sélectionné"})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # Lire le contenu du fichier
            text = ""
            if filename.endswith(('.docx', '.doc')):
                try:
                    from docx import Document
                    doc = Document(file_path)
                    text = "\n".join([para.text for para in doc.paragraphs])
                except ImportError:
                    text = f"[Contenu du document {filename} - Module python-docx manquant]"
            elif filename.endswith('.pdf'):
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        text = "\n".join([page.extract_text() for page in pdf_reader.pages])
                except ImportError:
                    text = f"[Contenu du PDF {filename} - Module PyPDF2 manquant]"
            elif filename.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            elif filename.endswith(('.xlsx', '.xls')):
                # Pour les fichiers Excel
                df = pd.read_excel(file_path)
                text = df.to_string()
            else:
                text = f"[Contenu du fichier {filename}]"
            
            print(f"Document analysé: {filename}, taille: {len(text)} caractères")
            
            return jsonify({
                "success": True,
                "data": {
                    "fileName": filename,
                    "mimeType": file.mimetype,
                    "text": text
                }
            })
        except Exception as e:
            print(f"Erreur lors de l'analyse du document: {e}")
            return jsonify({"success": False, "message": f"Erreur lors de l'analyse du document: {str(e)}"})
    
    return jsonify({"success": False, "message": "Type de fichier non autorisé"})

@app.route('/api/files/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/ia/analyze-document', methods=['POST'])
def api_analyze_document():
    data = request.json
    document_text = data.get('documentText', '')
    
    print(f"=== ANALYSE DOCUMENT API ===")
    print(f"Longueur du texte reçu: {len(document_text)}")
    
    if not document_text:
        return jsonify({"success": False, "message": "Le texte du document est requis"})
    
    # Analyser avec Prisme AI
    try:
        print("Appel de analyze_document...")
        analysis_results = analyze_document(document_text, app.config['PRISME_API_KEY'])
        print(f"Résultat d'analyse: {len(analysis_results.get('keywords', []))} mots-clés, {len(analysis_results.get('selectionCriteria', []))} critères de sélection")
        return jsonify({"success": True, "data": analysis_results})
    except Exception as e:
        print(f"Erreur dans analyze_document: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/ia/find-matching-companies', methods=['POST'])
def api_find_matching_companies():
    data = request.json
    criteria = data.get('criteria', [])
    
    print(f"=== RECHERCHE ENTREPRISES ===")
    print(f"Nombre de critères reçus: {len(criteria)}")
    print(f"Nombre d'entreprises disponibles: {len(COMPANIES)}")
    
    if not criteria:
        return jsonify({"success": False, "message": "Les critères sont requis"})
    
    if not COMPANIES:
        return jsonify({"success": False, "message": "Aucune entreprise disponible dans la base de données"})
    
    try:
        # Utiliser les entreprises pré-chargées
        matched_companies = match_companies(COMPANIES, criteria)
        print(f"Nombre d'entreprises correspondantes trouvées: {len(matched_companies)}")
        
        if matched_companies:
            print(f"Première entreprise correspondante: {matched_companies[0]['name']} (score: {matched_companies[0]['score']})")
        
        return jsonify({"success": True, "data": matched_companies})
    except Exception as e:
        print(f"Erreur lors du matching: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/ia/agent-query', methods=['POST'])
def api_agent_query():
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({"success": False, "message": "La question est requise"})
    
    try:
        # Interroger l'agent Prisme AI
        answer = get_agent_answer(question, app.config['PRISME_API_KEY'], app.config['PRISME_AGENT_ID'])
        return jsonify({"success": True, "data": {"answer": answer}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/documents/generate', methods=['POST'])
def api_generate_document():
    data = request.json
    template_type = data.get('templateType')
    project_data = data.get('projectData', {})
    companies = data.get('companies', [])
    
    if not template_type:
        return jsonify({"success": False, "message": "Le type de document est requis"})
    
    try:
        document_content = generate_document(
            template_type, 
            project_data, 
            app.config['PRISME_API_KEY']
        )
        
        # Enregistrer le document généré
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        project_id = project_data.get('id', 'projet').replace(' ', '_')
        
        # Déterminer l'extension du fichier
        extension = 'docx'
        if template_type == 'grilleEvaluation':
            extension = 'xlsx'
        
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
        file_path = os.path.join(app.config['GENERATED_DOCS'], filename)
        
        # Écrire le contenu dans un fichier
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(document_content)
        
        return jsonify({
            "success": True,
            "data": {
                "fileName": filename,
                "fileUrl": f"/api/documents/download/{filename}",
                "type": extension
            }
        })
    except Exception as e:
        print(f"Erreur lors de la génération du document: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/documents/download/<filename>')
def download_document(filename):
    return send_from_directory(app.config['GENERATED_DOCS'], filename)

@app.route('/api/documents/template/download/<filename>')
def download_template_document(filename):
    return send_from_directory(app.config['TEMPLATE_DOCS'], filename)

# ================================================
# ROUTES API POUR LA BASE DE DONNÉES
# ================================================

@app.route('/api/database/import-excel', methods=['POST'])
def import_excel():
    """Import d'entreprises depuis un fichier Excel"""
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Aucun fichier fourni"})
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"success": False, "message": "Aucun fichier sélectionné"})
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({"success": False, "message": "Format de fichier non supporté. Utilisez .xlsx ou .xls"})
    
    try:
        # Sauvegarder temporairement le fichier
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{filename}")
        file.save(temp_path)
        
        print(f"Import Excel: fichier sauvé temporairement à {temp_path}")
        
        # Charger les entreprises depuis le fichier
        new_companies = load_companies_from_excel(temp_path)
        print(f"Import Excel: {len(new_companies)} entreprises extraites")
        
        # Supprimer le fichier temporaire
        os.remove(temp_path)
        
        if new_companies:
            # Mettre à jour la liste globale des entreprises
            global COMPANIES
            # Fusionner avec les entreprises existantes (éviter les doublons par nom)
            existing_names = {comp['name'].lower() for comp in COMPANIES}
            added_count = 0
            
            for company in new_companies:
                if company['name'].lower() not in existing_names:
                    COMPANIES.append(company)
                    added_count += 1
            
            print(f"Import Excel: {added_count} nouvelles entreprises ajoutées")
            print(f"Total entreprises après import: {len(COMPANIES)}")
            
            return jsonify({
                "success": True, 
                "message": f"{added_count} nouvelles entreprises importées",
                "imported": added_count,
                "total": len(new_companies)
            })
        else:
            return jsonify({"success": False, "message": "Aucune entreprise trouvée dans le fichier"})
            
    except Exception as e:
        print(f"Erreur lors de l'import Excel: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"Erreur lors de l'import: {str(e)}"})

@app.route('/api/database/delete-company', methods=['DELETE'])
def delete_company():
    """Supprime une entreprise"""
    data = request.json
    company_id = data.get('id')
    
    if not company_id:
        return jsonify({"success": False, "message": "L'identifiant de l'entreprise est requis"})
    
    global COMPANIES
    # Trouver et supprimer l'entreprise
    original_count = len(COMPANIES)
    COMPANIES = [company for company in COMPANIES if company['id'] != company_id]
    
    if len(COMPANIES) < original_count:
        print(f"Entreprise {company_id} supprimée. Total: {len(COMPANIES)}")
        return jsonify({"success": True, "message": "Entreprise supprimée avec succès"})
    else:
        return jsonify({"success": False, "message": "Entreprise non trouvée"})

@app.route('/api/database/update-company', methods=['POST'])
def update_company():
    """Met à jour une entreprise existante"""
    data = request.json
    company_id = data.get('id')
    
    if not company_id:
        return jsonify({"success": False, "message": "L'identifiant de l'entreprise est requis"})
    
    # Trouver l'entreprise dans la liste
    for i, company in enumerate(COMPANIES):
        if company['id'] == company_id:
            # Mettre à jour les champs fournis
            for key, value in data.items():
                if key != 'id':
                    COMPANIES[i][key] = value
            
            print(f"Entreprise {company_id} mise à jour: {COMPANIES[i]['name']}")
            return jsonify({"success": True, "data": COMPANIES[i]})
    
    return jsonify({"success": False, "message": "Entreprise non trouvée"})

@app.route('/api/database/add-company', methods=['POST'])
def add_company():
    """Ajoute une nouvelle entreprise"""
    data = request.json
    company_name = data.get('name')
    
    if not company_name:
        return jsonify({"success": False, "message": "Le nom de l'entreprise est requis"})
    
    # Créer un nouvel ID
    company_id = f"ENT_{str(len(COMPANIES) + 1).zfill(3)}"
    
    # Créer la nouvelle entreprise avec le nouveau format
    new_company = {
        'id': company_id,
        'name': company_name,
        'domain': data.get('domain', 'Non spécifié'),
        'location': data.get('location', 'Non spécifié'),
        'certifications': data.get('certifications', []),
        'ca': data.get('ca', 'Non spécifié'),
        'employees': data.get('employees', 'Non spécifié'),
        'contact': data.get('contact', {}),
        'experience': data.get('experience', 'Non spécifié'),
        'score': 0
    }
    
    # Ajouter à la liste
    COMPANIES.append(new_company)
    
    print(f"Nouvelle entreprise ajoutée: {company_name} (ID: {company_id})")
    print(f"Total entreprises: {len(COMPANIES)}")
    
    return jsonify({"success": True, "data": new_company})

@app.route('/api/support/send-message', methods=['POST'])
def send_support_message():
    data = request.json
    name = data.get('name', '')
    email = data.get('email', '')
    subject = data.get('subject', '')
    message = data.get('message', '')
    
    if not name or not email or not subject or not message:
        return jsonify({"success": False, "message": "Tous les champs sont requis"})
    
    try:
        # Enregistrer le message dans un fichier pour démonstration
        support_dir = 'support_messages'
        os.makedirs(support_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        message_file = os.path.join(support_dir, f"message_{timestamp}.txt")
        
        with open(message_file, 'w', encoding='utf-8') as f:
            f.write(f"De: {name} ({email})\n")
            f.write(f"Sujet: {subject}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\n")
            f.write(message)
        
        return jsonify({
            "success": True,
            "message": "Message envoyé avec succès"
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Erreur lors de l'envoi du message: {str(e)}"})

# Démarrer l'application
if __name__ == '__main__':
    print("=== DÉMARRAGE DU SERVEUR ===")
    print(f"Nombre d'entreprises chargées: {len(COMPANIES)}")
    print("Serveur démarré sur http://localhost:5001")
    print("=== READY ===")
    app.run(debug=True, host='0.0.0.0', port=5001)