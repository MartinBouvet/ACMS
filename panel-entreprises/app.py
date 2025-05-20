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
app.config['COMPANIES_EXCEL'] = os.path.join('data', 'ACMS Publipostage FINAL V4.xlsx')
app.config['PRISME_API_KEY'] = 'cec930ebb79846da94d2cf5028177995'
app.config['PRISME_AGENT_ID'] = '67f785d59e82260f684a217a'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

# Créer les dossiers nécessaires
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_DOCS'], exist_ok=True)
os.makedirs(app.config['TEMPLATE_DOCS'], exist_ok=True)
os.makedirs('data', exist_ok=True)

# Charger les entreprises à partir du fichier Excel
COMPANIES = []
try:
    COMPANIES = load_companies_from_excel(app.config['COMPANIES_EXCEL'])
    print(f"Chargé {len(COMPANIES)} entreprises depuis le fichier Excel")
except Exception as e:
    print(f"Erreur lors du chargement du fichier Excel: {e}")
    print(traceback.format_exc())

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
        return jsonify({"success": True, "data": COMPANIES})
    except Exception as e:
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
            
            return jsonify({
                "success": True,
                "data": {
                    "fileName": filename,
                    "mimeType": file.mimetype,
                    "text": text
                }
            })
        except Exception as e:
            return jsonify({"success": False, "message": f"Erreur lors de l'analyse du document: {str(e)}"})
    
    return jsonify({"success": False, "message": "Type de fichier non autorisé"})

@app.route('/api/files/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/ia/analyze-document', methods=['POST'])
def api_analyze_document():
    data = request.json
    document_text = data.get('documentText', '')
    
    if not document_text:
        return jsonify({"success": False, "message": "Le texte du document est requis"})
    
    # Analyser avec Prisme AI
    try:
        analysis_results = analyze_document(document_text, app.config['PRISME_API_KEY'])
        return jsonify({"success": True, "data": analysis_results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/ia/find-matching-companies', methods=['POST'])
def api_find_matching_companies():
    data = request.json
    criteria = data.get('criteria', [])
    
    if not criteria:
        return jsonify({"success": False, "message": "Les critères sont requis"})
    
    try:
        # Utiliser les entreprises pré-chargées
        matched_companies = match_companies(COMPANIES, criteria)
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

@app.route('/api/database/update-company', methods=['POST'])
def update_company():
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
            
            return jsonify({"success": True, "data": COMPANIES[i]})
    
    return jsonify({"success": False, "message": "Entreprise non trouvée"})

@app.route('/api/database/add-company', methods=['POST'])
def add_company():
    data = request.json
    company_name = data.get('name')
    
    if not company_name:
        return jsonify({"success": False, "message": "Le nom de l'entreprise est requis"})
    
    # Créer un nouvel ID
    company_id = str(len(COMPANIES) + 1).zfill(3)
    
    # Créer la nouvelle entreprise
    new_company = {
        'id': company_id,
        'name': company_name,
        'location': data.get('location', 'Non spécifié'),
        'certifications': data.get('certifications', []),
        'ca': data.get('ca', 'Non spécifié'),
        'employees': data.get('employees', 'Non spécifié'),
        'experience': data.get('experience', 'Non spécifié')
    }
    
    # Ajouter à la liste
    COMPANIES.append(new_company)
    
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
    
    # Dans une implémentation complète, on enverrait un email
    # Ici, on simule un succès
    
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
    print("Démarrage du serveur sur le port 5001...")
    app.run(debug=True, host='0.0.0.0', port=5001)
    print("Serveur arrêté")