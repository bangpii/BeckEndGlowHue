from flask import Blueprint, request, jsonify, send_from_directory, current_app
import os
import uuid
import shutil
from components.skin_tone import change_skin_tone

foto_bp = Blueprint("foto", __name__)
user_sessions = {}

@foto_bp.route("/upload", methods=["POST"])
def upload_file():
    print("=== UPLOAD ENDPOINT HIT ===")
    
    if "file" not in request.files:
        print("No file part in request")
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    print(f"File received: {file.filename}")
    
    if file.filename == "":
        print("Empty filename")
        return jsonify({"error": "No selected file"}), 400

    # Generate unique session ID
    session_id = str(uuid.uuid4())
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    
    # Ensure upload folder exists
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Save original file
    original_filename = f"{session_id}_original_{file.filename}"
    original_filepath = os.path.join(upload_folder, original_filename)
    
    try:
        file.save(original_filepath)
        print(f"File saved to: {original_filepath}")
        
        # Verify file was saved
        if not os.path.exists(original_filepath):
            raise Exception("File failed to save")
            
    except Exception as e:
        print(f"Error saving file: {str(e)}")
        return jsonify({"error": f"Failed to save file: {str(e)}"}), 500

    # Initialize user session
    user_sessions[session_id] = {
        "original": original_filepath,
        "current": original_filepath,
        "filename": file.filename
    }
    
    print(f"Session created: {session_id}")
    
    return jsonify({
        "session_id": session_id,
        "filename": file.filename,
        "url": f"http://localhost:5000/uploads/{original_filename}"
    }), 200

@foto_bp.route("/apply_color", methods=["POST"])
def apply_color():
    print("=== APPLY COLOR ENDPOINT HIT ===")
    
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
        print(f"JSON data received: {data}")
    else:
        data = request.form
        print(f"Form data received: {data}")
    
    hex_color = data.get("color")
    session_id = data.get("session_id")

    print(f"Session ID: {session_id}")
    print(f"Hex Color: {hex_color}")

    if not session_id:
        print("Missing session_id")
        return jsonify({"error": "Missing session_id"}), 400
        
    if session_id not in user_sessions:
        print(f"Invalid session: {session_id}")
        return jsonify({"error": "Invalid session"}), 400

    if not hex_color:
        print("Missing color")
        return jsonify({"error": "Missing color"}), 400

    try:
        # Get original file path
        original_path = user_sessions[session_id]["original"]
        print(f"Original path: {original_path}")
        
        # Verify original file exists
        if not os.path.exists(original_path):
            print("Original file not found")
            return jsonify({"error": "Original file not found"}), 400
        
        # Generate unique filename untuk setiap perubahan
        unique_id = str(uuid.uuid4())[:8]
        temp_filename = f"{session_id}_temp_{unique_id}_{user_sessions[session_id]['filename']}"
        temp_original = os.path.join(os.path.dirname(original_path), temp_filename)
        
        # Copy original untuk processing
        shutil.copy2(original_path, temp_original)
        print(f"Temp file created: {temp_original}")
        
        # Apply color change
        print("Calling change_skin_tone...")
        output_path = change_skin_tone(temp_original, hex_color)
        print(f"Output path: {output_path}")
        
        # Update current file in session
        user_sessions[session_id]["current"] = output_path
        
        # Clean up temp file
        if os.path.exists(temp_original):
            os.remove(temp_original)
            print("Temp file cleaned up")
        
        # Generate URL dengan timestamp untuk cache busting
        result_url = f"http://localhost:5000/uploads/{os.path.basename(output_path)}?t={uuid.uuid4().hex[:8]}"
        print(f"Result URL: {result_url}")
            
        return jsonify({
            "success": True,
            "result_url": result_url,
            "session_id": session_id
        }), 200
        
    except Exception as e:
        print(f"Error in apply_color: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

@foto_bp.route("/reset_color", methods=["POST"])
def reset_color():
    print("=== RESET COLOR ENDPOINT HIT ===")
    
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
        
    session_id = data.get("session_id")
    print(f"Reset for session: {session_id}")

    if not session_id or session_id not in user_sessions:
        return jsonify({"error": "Invalid session"}), 400

    original_path = user_sessions[session_id]["original"]
    user_sessions[session_id]["current"] = original_path
    
    original_url = f"http://localhost:5000/uploads/{os.path.basename(original_path)}?t={uuid.uuid4().hex[:8]}"
    
    return jsonify({
        "success": True,
        "original_url": original_url,
        "session_id": session_id
    }), 200

@foto_bp.route("/get_skin_recommendations", methods=["POST"])
def get_skin_recommendations():
    data = request.get_json()
    hex_color = data.get("skin_tone")
    undertone = data.get("undertone")
    
    if not hex_color or not undertone:
        return jsonify({"error": "Missing skin_tone or undertone"}), 400
    
    # Convert HEX to RGB
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # Calculate brightness
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    
    # Determine skin type based on brightness
    if brightness < 85:
        skin_type = "DARK"
        skin_desc = "hitam/gelap"
    elif brightness < 170:
        skin_type = "MEDIUM" 
        skin_desc = "sawo matang"
    else:
        skin_type = "LIGHT"
        skin_desc = "putih/cerah"
    
    # Recommendations based on skin type and undertone
    recommendations = {
        "DARK_COOL": [
            {"name": "Deep Berry", "hex": "#B76E79"},
            {"name": "Rose Mauve", "hex": "#C08081"}, 
            {"name": "Rich Berry", "hex": "#8B004B"},
            {"name": "Dark Wine", "hex": "#5C0D0D"}
        ],
        "DARK_NEUTRAL": [
            {"name": "Deep Taupe", "hex": "#8B7D6B"},
            {"name": "Muted Mauve", "hex": "#915F6D"},
            {"name": "Espresso", "hex": "#4B3621"},
            {"name": "Burgundy", "hex": "#800020"}
        ],
        "DARK_WARM": [
            {"name": "Deep Bronze", "hex": "#8B4000"},
            {"name": "Chocolate", "hex": "#5C4033"},
            {"name": "Maroon", "hex": "#800000"},
            {"name": "Copper", "hex": "#CD7F32"}
        ],
        "MEDIUM_COOL": [
            {"name": "Soft Blue", "hex": "#A3C1D1"},
            {"name": "Rose Mauve", "hex": "#C08081"},
            {"name": "Lavender", "hex": "#7851A9"},
            {"name": "Ruby", "hex": "#9B111E"}
        ],
        "MEDIUM_NEUTRAL": [
            {"name": "Taupe", "hex": "#C0A080"},
            {"name": "Dusty Rose", "hex": "#DCAE96"},
            {"name": "Warm Gray", "hex": "#8B7D6B"},
            {"name": "Mauve", "hex": "#915F6D"}
        ],
        "MEDIUM_WARM": [
            {"name": "Caramel", "hex": "#D2A679"},
            {"name": "Copper", "hex": "#B87333"},
            {"name": "Bronze", "hex": "#AF6E4D"},
            {"name": "Golden", "hex": "#996515"}
        ],
        "LIGHT_COOL": [
            {"name": "Light Blue", "hex": "#DDEEFF"},
            {"name": "Pink", "hex": "#FFC0CB"},
            {"name": "Lavender", "hex": "#E6E6FA"},
            {"name": "Cool Nude", "hex": "#F0E6F6"}
        ],
        "LIGHT_NEUTRAL": [
            {"name": "Beige", "hex": "#F5F5DC"},
            {"name": "Peach", "hex": "#FFDAB9"},
            {"name": "Taupe", "hex": "#483C32"},
            {"name": "Warm Peach", "hex": "#FFE5B4"}
        ],
        "LIGHT_WARM": [
            {"name": "Light Gold", "hex": "#FFE4B5"},
            {"name": "Apricot", "hex": "#FFCC99"},
            {"name": "Coral", "hex": "#E2725B"},
            {"name": "Soft Peach", "hex": "#FBCEB1"}
        ]
    }
    
    skin_key = f"{skin_type}_{undertone}"
    recommended_colors = recommendations.get(skin_key, [])
    
    return jsonify({
        "skin_type": skin_type,
        "skin_description": skin_desc,
        "undertone": undertone,
        "recommended_colors": recommended_colors,
        "message": f"Rekomendasi untuk kulit {skin_desc} dengan undertone {undertone}"
    }), 200

def classify_undertone(hex_color):
    if not hex_color or hex_color == "RESET":
        return "NEUTRAL"
        
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return "NEUTRAL"
        
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        if r > g and r > b and r - g > 30:
            return "WARM"
        elif b > r and b > g and b - r > 20:
            return "COOL"
        else:
            return "NEUTRAL"
    except:
        return "NEUTRAL"

@foto_bp.route("/uploads/<path:filename>")
def get_uploaded_file(filename):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    print(f"Serving file: {filename} from {upload_folder}")
    return send_from_directory(upload_folder, filename)

@foto_bp.route("/debug_sessions", methods=["GET"])
def debug_sessions():
    return jsonify({
        "sessions": user_sessions,
        "count": len(user_sessions)
    }), 200