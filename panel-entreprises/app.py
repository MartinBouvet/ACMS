# app.py
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
app.config['TEMPLATE_DOCS'] = 'templates_docs'  # Nouveau dossier pour les documents types
app.config['COMPANIES_EXCEL'] = os.path.join('data', 'ACMS Publipostage FINAL V4.xlsx')
app.config['MISTRAL_API_KEY'] = 'cec930ebb79846da94d2cf5028177995'
app.config['MISTRAL_AGENT_ID'] = '67f785d59e82260f684a217a'
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

# Routes pour les pages web
@app.route('/')
def index():
    return render_template('pages/dashboard.html', page='dashboard')

@app.route('/dashboard')
def dashboard():
    return render_template('pages/dashboard.html', page='dashboard')

@app.route('/search')
def search():
    return render_template('pages/search.html', page='search')

@app.route('/database')
def database():
    return render_template('pages/database.html', page='database', companies=COMPANIES)

# Nouvelles routes pour les pages supplémentaires
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
            if os.path.isfile(file_path):
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

# Routes API existantes
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
    
    # Analyser avec Mistral AI
    try:
        analysis_results = analyze_document(document_text, app.config['MISTRAL_API_KEY'])
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
        # Interroger l'agent Mistral
        answer = get_agent_answer(question, app.config['MISTRAL_API_KEY'], app.config['MISTRAL_AGENT_ID'])
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
        document_info = create_document(
            template_type, 
            project_data, 
            companies,
            app.config['GENERATED_DOCS'],
            app.config['MISTRAL_API_KEY']
        )
        
        return jsonify({
            "success": True,
            "data": document_info
        })
    except Exception as e:
        print(f"Erreur lors de la génération du document: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/documents/download/<filename>')
def download_document(filename):
    return send_from_directory(app.config['GENERATED_DOCS'], filename)

# Nouvelles routes API pour les documents types
@app.route('/api/documents/template/upload', methods=['POST'])
def upload_template_document():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Aucun fichier fourni"})
        
    file = request.files['file']
    name = request.form.get('name', '')
    doc_type = request.form.get('type', 'autre')
    description = request.form.get('description', '')
    
    if file.filename == '':
        return jsonify({"success": False, "message": "Aucun fichier sélectionné"})
        
    if file and allowed_file(file.filename):
        # Créer un nom de fichier basé sur le type et le nom fourni
        base_name = secure_filename(name)
        extension = file.filename.rsplit('.', 1)[1].lower()
        
        # Ajouter un préfixe selon le type
        prefix_map = {
            'reglement': 'REG',
            'marche': 'MAR',
            'lettre': 'LET',
            'grille': 'GRIL',
            'autre': 'DOC'
        }
        prefix = prefix_map.get(doc_type, 'DOC')
        
        # Créer un horodatage
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Assembler le nom de fichier final
        filename = f"{prefix}_{base_name}_{timestamp}.{extension}"
        file_path = os.path.join(app.config['TEMPLATE_DOCS'], filename)
        
        # Enregistrer le fichier
        file.save(file_path)
        
        # Enregistrer les métadonnées (dans une implémentation complète, on utiliserait une base de données)
        # Ici, on utilise un fichier JSON simple pour démonstration
        metadata_file = os.path.join(app.config['TEMPLATE_DOCS'], 'metadata.json')
        metadata = {}
        
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except:
                metadata = {}
        
        metadata[filename] = {
            'name': name,
            'type': doc_type,
            'description': description,
            'uploadDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            "success": True,
            "message": "Document type téléversé avec succès",
            "data": {
                "id": f"doc_{len(metadata)}",
                "name": name,
                "fileName": filename,
                "type": doc_type,
                "url": f"/api/documents/template/download/{filename}"
            }
        })
    
    return jsonify({"success": False, "message": "Type de fichier non autorisé"})

@app.route('/api/documents/template/<document_id>', methods=['GET'])
def get_template_document(document_id):
    # Dans une implémentation complète, on récupérerait les détails du document depuis une base de données
    # Ici, on simule avec les métadonnées stockées dans un fichier JSON
    
    metadata_file = os.path.join(app.config['TEMPLATE_DOCS'], 'metadata.json')
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            # Trouver le document par ID
            for filename, doc_data in metadata.items():
                if f"doc_{list(metadata.keys()).index(filename) + 1}" == document_id:
                    return jsonify({
                        "success": True,
                        "data": {
                            "id": document_id,
                            "name": doc_data.get('name', filename),
                            "fileName": filename,
                            "type": doc_data.get('type', 'autre'),
                            "description": doc_data.get('description', ''),
                            "url": f"/api/documents/template/download/{filename}",
                            # La prévisualisation nécessiterait une conversion du document
                            # Dans une implémentation complète, cela pourrait être fait avec des librairies appropriées
                            "previewHtml": None
                        }
                    })
        except Exception as e:
            return jsonify({"success": False, "message": f"Erreur lors de la récupération du document: {str(e)}"})
    
    return jsonify({"success": False, "message": "Document non trouvé"})

@app.route('/api/documents/template/<document_id>', methods=['DELETE'])
def delete_template_document(document_id):
    # Dans une implémentation complète, on récupérerait les détails du document depuis une base de données
    # Ici, on simule avec les métadonnées stockées dans un fichier JSON
    
    metadata_file = os.path.join(app.config['TEMPLATE_DOCS'], 'metadata.json')
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            # Trouver le document par ID
            for filename, doc_data in list(metadata.items()):
                if f"doc_{list(metadata.keys()).index(filename) + 1}" == document_id:
                    # Supprimer le fichier
                    file_path = os.path.join(app.config['TEMPLATE_DOCS'], filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    
                    # Supprimer les métadonnées
                    del metadata[filename]
                    
                    # Enregistrer les métadonnées mises à jour
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)
                    
                    return jsonify({
                        "success": True,
                        "message": "Document supprimé avec succès"
                    })
        except Exception as e:
            return jsonify({"success": False, "message": f"Erreur lors de la suppression du document: {str(e)}"})
    
    return jsonify({"success": False, "message": "Document non trouvé"})

@app.route('/api/documents/template/download/<filename>')
def download_template_document(filename):
    return send_from_directory(app.config['TEMPLATE_DOCS'], filename)

# Route API pour le support
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