# app.py
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
import os
import json
import pandas as pd
from werkzeug.utils import secure_filename
import traceback

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
app.config['COMPANIES_EXCEL'] = os.path.join('data', 'ACMS Publipostage FINAL V4.xlsx')
app.config['MISTRAL_API_KEY'] = 'cec930ebb79846da94d2cf5028177995'
app.config['MISTRAL_AGENT_ID'] = '67f785d59e82260f684a217a'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

# Créer les dossiers nécessaires
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_DOCS'], exist_ok=True)
os.makedirs('data', exist_ok=True)
# Au début d'app.py
if __name__ == '__main__':
    print("Démarrage du serveur...")
    app.run(debug=True, host='0.0.0.0', port=5000)
    print("Serveur arrêté")
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
    return render_template('index.html', page='dashboard')

@app.route('/dashboard')
def dashboard():
    return render_template('pages/dashboard.html', page='dashboard')

@app.route('/search')
def search():
    return render_template('pages/search.html', page='search')

@app.route('/database')
def database():
    return render_template('pages/database.html', page='database', companies=COMPANIES)

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

# Démarrer l'application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)