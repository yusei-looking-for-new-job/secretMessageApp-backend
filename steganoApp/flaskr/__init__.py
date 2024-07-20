from flask import Flask
app = Flask(__name__,static_folder='/home/ec2-user/steganoApp/build/web')
from flaskr.main import allowed_file, convert_to_rgb, embed_string, extract_string