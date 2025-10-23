from flask import Flask
from flask_cors import CORS
import os

# import blueprint dari components/fhoto.py
from components.fhoto import foto_bp

app = Flask(__name__)
CORS(app)

# Folder upload global
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Pastikan folder uploads ada
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Daftarkan blueprint
app.register_blueprint(foto_bp, url_prefix="/")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
