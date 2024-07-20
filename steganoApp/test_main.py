import pytest
import io
from PIL import Image
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flaskr import app, allowed_file, convert_to_rgb, embed_string, extract_string
from base64 import b64encode

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_allowed_file():
    assert allowed_file('test.png') == True
    assert allowed_file('test.jpg') == True
    assert allowed_file('test.jpeg') == True
    assert allowed_file('test.gif') == True
    assert allowed_file('test.txt') == False
    assert allowed_file('test') == False

def test_convert_to_rgb():
    rgb_image = Image.new('RGB', (100, 100))
    rgba_image = Image.new('RGBA', (100, 100))
    
    assert convert_to_rgb(rgb_image).mode == 'RGB'
    assert convert_to_rgb(rgba_image).mode == 'RGB'

def test_embed_and_extract_string():
    test_string = 'test string'
    image = Image.new('RGB', (100, 100))
    
    embedded_image = embed_string(image, test_string)
    extracted_string = extract_string(embedded_image)
    
    assert extracted_string == test_string

def test_serve_index(client):
    response = client.get('/')
    assert response.status_code == 200

def test_embed_api_valid(client):
    image = Image.new('RGB', (100, 100))
    image_file = io.BytesIO()
    image.save(image_file, format='PNG')
    image_file.seek(0)
    
    response = client.post(
        '/embed',
        data={
            'image': (image_file, 'test.png'),
            'string': 'test string'
        },
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 200
    assert response.mimetype == 'image/png'

def test_embed_api_no_file(client):
    response = client.post('/embed', data={})
    assert response.status_code == 400

def test_embed_api_invalid_extension(client):
    file = io.BytesIO(b"invalid file content")
    
    response = client.post(
        '/embed',
        data={
            'image': (file, 'test.txt'),
            'string': 'test string'
        },
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 400

def test_embed_api_string_size_exceed(client):
    image = Image.new('RGB', (100, 100))
    image_file = io.BytesIO()
    image.save(image_file, format='PNG')
    image_file.seek(0)
    
    response = client.post(
        '/embed',
        data={
            'image': (image_file, 'test.png'),
            'string': 'a' * 3000
        },
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 416

def test_extract_api_valid(client):
    test_string = 'test string'
    image = Image.new('RGB', (100, 100))
    embedded_image = embed_string(image, test_string)
    
    image_file = io.BytesIO()
    embedded_image.save(image_file, format='PNG')
    image_file.seek(0)
    
    response = client.post(
        '/extract',
        data={'image': (image_file, 'test.png')},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 200
    assert response.json['extracted_string'] == test_string

def test_extract_api_no_file(client):
    response = client.post('/extract', data={})
    assert response.status_code == 400

def test_extract_api_invalid_extension(client):
    file = io.BytesIO(b"invalid file content")
    
    response = client.post(
        '/extract',
        data={'image': (file, 'test.txt')},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 400

def test_serve_static_nonexistent_file(client):
    response = client.get('/static/test.txt')
    assert response.status_code == 404