from flaskr import app
from flask import render_template, jsonify
import base64
from io import BytesIO
from stegano import lsb
from PIL import Image
from flask_cors import CORS
from flask import Flask, send_from_directory, request, send_file
from werkzeug.utils import secure_filename
import os
from html import escape

# 許可されるファイル拡張子のリスト
#アプリ、webから送る場合はフロントでimage.jpgとするので念のため
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 最大ファイルサイズを設定(10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_to_rgb(image):
    if image.mode != 'RGB':
        image = image.convert('RGB')
    return image

def embed_string(image, string):
    encoded_string = base64.b64encode(string.encode('utf-8')).decode('utf-8')
    img_encoded = lsb.hide(image, encoded_string)
    return img_encoded

def extract_string(image):
    encoded_string = lsb.reveal(image)
    string = base64.b64decode(encoded_string.encode('utf-8')).decode('utf-8')
    return string

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/embed', methods=['POST'])
def embed_api():
    try:
        # ファイルの存在とサイズを確認
        if 'image' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        if file.content_length > MAX_FILE_SIZE:
            return jsonify({'error': 'File size exceeds the limit'}), 400

        image_data = file.read()
        string = request.form['string']

        # 文字列のサイズを制限
        if len(string.encode('utf-8')) > 3500:
            return jsonify({'error': 'String size exceeds the limit'}), 416

        # 入力文字列をエスケープ
        escaped_string = escape(string)

        img = Image.open(BytesIO(image_data))
        img_rgb = convert_to_rgb(img)
        img_encoded = embed_string(img_rgb, escaped_string)
        buffered = BytesIO()
        img_encoded.save(buffered, format="PNG")
        encoded_image_data = buffered.getvalue()
        return send_file(BytesIO(encoded_image_data), mimetype='image/png')
    except Exception as e:
        app.logger.error(f"Error in /embed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/extract', methods=['POST'])
def extract_api():
    try:
        # ファイルの存在とサイズを確認
        if 'image' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        if file.content_length > MAX_FILE_SIZE:
            return jsonify({'error': 'File size exceeds the limit'}), 413

        image_data = file.read()
        img = Image.open(BytesIO(image_data))
        extracted_string = extract_string(img)

        # エスケープ処理を追加
        escaped_string = escape(extracted_string)

        response = jsonify({'extracted_string': escaped_string})
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)