import os
import uuid
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from deepfake_detector import NeuralVoiceTripwire

app = Flask(__name__)

analyzer = NeuralVoiceTripwire()

# Ensure a dedicated temp directory exists for cleanly handling files
TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No audio data received"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty file submitted"}), 400

    # 1. Secure the filename and extract extension
    original_filename = secure_filename(file.filename)
    ext = os.path.splitext(original_filename)[1]

    # Browsers often record in .webm or .ogg; default to .webm if missing
    if not ext:
        ext = ".webm"

    # 2. Create a unique, collision-proof temporary filepath
    unique_filename = f"audio_{uuid.uuid4().hex}{ext}"
    temp_file_path = os.path.join(TEMP_DIR, unique_filename)

    file.save(temp_file_path)

    try:
        # Run neural classifier
        results = analyzer.analyze(temp_file_path)

        is_fake = results["verdict"] == "RED_SPOOF"
        confidence = results["confidence_percent"]

        if is_fake:
            message = f"🔴 {confidence}% likely AI-generated"
        else:
            message = f"🟢 {confidence}% likely real human voice"

        if results.get("duration_warning"):
            message += f" (⚠ {results['duration_warning']})"

        return jsonify({
            "is_deepfake": is_fake,
            "confidence": confidence,
            "raw_result": results["mathematical_metrics"],
            "message": message
        })

    except Exception as e:
        print(f"\n[!] Backend Error: {str(e)}\n")
        return jsonify({"error": str(e)}), 500

    finally:
        # Clean up the specific temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
