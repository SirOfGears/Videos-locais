from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from flask_socketio import SocketIO
import os
import json
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')  # Usando o caminho correto para arquivos estáticos
socketio = SocketIO(app)

db_file = os.path.join(app.root_path, 'database', 'videos.json')

# Criar diretórios necessários caso não existam
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.dirname(db_file), exist_ok=True)

# Criar arquivo de banco de dados se não existir
if not os.path.exists(db_file):
    with open(db_file, 'w') as f:
        json.dump({}, f)

# Função para carregar os vídeos do banco
def load_videos():
    with open(db_file, 'r') as f:
        return json.load(f)

# Função para salvar dados no banco de dados
def save_videos(data):
    with open(db_file, 'w') as f:
        json.dump(data, f, indent=4)

# Rota principal
@app.route('/')
def index():
    return render_template('index.html')

# Rota para o canal de vídeos
@app.route('/channel/<channel_code>')
def channel(channel_code):
    videos = load_videos().get(channel_code, [])
    return render_template('channel.html', channel_code=channel_code, videos=videos)

# Rota para upload de vídeos
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    channel_code = request.form['channel_code']
    title = request.form.get('title', 'Vídeo sem título')
    
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    filename = file.filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Atualizar banco de dados com o novo vídeo
    videos = load_videos()
    if channel_code not in videos:
        videos[channel_code] = []
    # armazenar o nome no banco de dados
    videos[channel_code].append({'title': title, 'file': filename})
    save_videos(videos)
    
    return redirect(url_for('channel', channel_code=channel_code))

# Rota para rodar vídeos a partir da pasta uploads
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Rota para escolher um vídeo aleatório
def random_video(channel_code):
    videos = load_videos().get(channel_code, [])
    
    if not videos:
        return redirect(url_for('channel', channel_code=channel_code))  # Se não existir vídeos, volta para a página do canal
    
    selected_video = random.choice(videos)  # Escolhe um vídeo aleatório
    return redirect(url_for('uploaded_file', filename=selected_video['file']))  # Redireciona para o vídeo

@app.route('/<channel_code>/random')
def random_video_route(channel_code):
    return random_video(channel_code)

if __name__ == '__main__':
    socketio.run(app, host='seuipv4aqui', port=5000, debug=True)
