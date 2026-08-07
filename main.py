import os
from flask import Flask, render_template, request, jsonify
from test import ComprehensiveVoiceTripwire

app = Flask(__name__)
analyzer = ComprehensiveVoiceTripwire()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Retain extension for correct librosa decoder selection
    ext = os.path.splitext(file.filename)[1]
    if not ext:
        ext = ".wav"

    temp_file_path = f"temp_upload{ext}"
    file.save(temp_file_path)

    try:
        results = analyzer.analyze(temp_file_path)

        is_fake = results["verdict"] == "RED_SPOOF"
        confidence = results["confidence_percent"]

        if is_fake:
            message = f"🔴 {confidence}% likely AI-generated"
        else:
            message = f"🟢 {confidence}% likely real human voice"

        return jsonify({
            "is_deepfake": is_fake,
            "confidence": confidence,
            "raw_result": results["mathematical_metrics"],
            "message": message
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)