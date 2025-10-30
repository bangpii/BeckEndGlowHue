from flask import Flask, jsonify
from flask_cors import CORS
import os

# import blueprint dari components/fhoto.py
from components.fhoto import foto_bp

app = Flask(__name__)

# Konfigurasi CORS untuk semua origin
CORS(app, origins=["*"])

# Folder upload global
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Konfigurasi tambahan untuk production
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Pastikan folder uploads ada
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Daftarkan blueprint
app.register_blueprint(foto_bp, url_prefix="/")

@app.route("/")
def home():
    return jsonify({"message": "GlowHue Backend API", "status": "running"})

@app.route("/health")
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)