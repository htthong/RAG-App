from flask import Flask
from flask import jsonify
from flask import request
from flask import session
from flask import render_template
from flask import send_from_directory
from flask_cors import CORS
import uuid
import logging
import sys
from model import init_index_pdf_file, init_index_pdf_folder, init_index_url
from model import init_conversation
from model import chat, reset_chromadb
from config import *
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'  # Required for session management

UPLOAD_FOLDER = 'uploads' 
if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)
SESSION_TIMEOUT = timedelta(minutes=30)  # Session timeout duration

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/api/question', methods=['POST'])
def post_question():
    json = request.get_json(silent=True)
    question = json['question']
    user_id = json['user_id']
    logging.info("post question `%s` for user `%s`", question, user_id)
    print("Question:", question)
    resp = chat(question, user_id)
    data = {'answer':resp}

    return jsonify({'reply': resp})
    return jsonify(data), 200

@app.route('/get-response', methods=['POST'])
def get_response():
    user_message = request.json.get('message')
    # Add your response logic here
    bot_reply = f"Received your message: {user_message}"
    return jsonify({'reply': bot_reply})

@app.route('/chat')
def index():
    return render_template('chat.html')

@app.route('/')
def index2():
    return render_template('chat.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        session_id = session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
        
        filename = session_id + '_' + file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        file.save(filepath)
        init_index_pdf_file(filepath)
        return jsonify({"filename": filename, "filepath": filepath}), 200
    
    return jsonify({"error": "File type not allowed"}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    session_id = session.get('session_id')
    if session_id:
        files_to_remove = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith(session_id + '_')]
        for file in files_to_remove:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))
        session.pop('session_id', None)  # Remove the session ID
        return jsonify({"status": "Files cleaned up"}), 200
    return jsonify({"error": "No session ID found"}), 400

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(filepath):
        os.remove(filepath)
        return jsonify({"status": "File deleted"}), 200
    return jsonify({"error": "File not found"}), 404

@app.route('/reset_db')
def reset_db():
    reset_chromadb()
    upload_path = "./uploads"
    session_id = str(session.get('session_id'))
    for path in os.listdir(upload_path):
        if session_id in path:
            os.remove(os.path.join(upload_path, path))
    return "None"

def cleanup_expired_sessions():
    """Function to cleanup files of expired sessions."""
    now = datetime.now()
    for file in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, file)
        if os.path.isfile(file_path):
            # Check for expired session files (e.g., older than SESSION_TIMEOUT)
            # Implement your logic here
            pass

if __name__ == '__main__':
    init_index_pdf_folder()
    init_conversation()
    app.run(host='0.0.0.0', port=HTTP_PORT, debug=True)
