from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import os, subprocess
from threading import Thread
import requests

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Track last upload (filename saved here). Used by view_pdf and pipeline.
LAST_UPLOAD_FILE = os.path.join(UPLOAD_FOLDER, "last_upload.txt")
def write_last_upload(name: str):
    try:
        with open(LAST_UPLOAD_FILE, 'w', encoding='utf-8') as f:
            f.write(name)
    except Exception as e:
        print(f"Could not write last upload file: {e}")

def read_last_upload() -> str:
    if not os.path.exists(LAST_UPLOAD_FILE):
        return ""
    try:
        with open(LAST_UPLOAD_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception:
        return ""

@app.route("/")
def index():
    return render_template("index.html")

def _run_pipeline(selected_type: str):
    try:
        env = {**os.environ, "QUESTION_TYPE": selected_type}
        subprocess.run(["python", "run_pipeline.py"], check=True, env=env)
    except Exception as e:
        print(f"Pipeline error: {e}")


@app.route("/prepare", methods=["POST"])
def prepare():
    selected_type = request.form.get("question_type", "")
    input_mode = request.form.get("input_mode", "file")
    filepath = os.path.join(UPLOAD_FOLDER, "sample.pdf")
    
    # Handle file upload mode
    if input_mode == "file":
        file = request.files.get("pdf")
        if not file or file.filename == "":
            return "No file uploaded!", 400
        # Save using the original filename but make it unique to avoid caching/overwrites
        from werkzeug.utils import secure_filename
        import time
        fname = secure_filename(file.filename)
        unique_name = f"{int(time.time())}_{fname}"
        save_path = os.path.join(UPLOAD_FOLDER, unique_name)
        file.save(save_path)
        # Record the saved filename so other parts of the app use the correct file
        write_last_upload(unique_name)
        print(f"✅ Uploaded and saved as: {save_path}")
    
    # Handle text mode
    elif input_mode == "text":
        text_content = request.form.get("text_content", "").strip()
        if not text_content:
            return "No text content provided!", 400
        
        # Save pasted text to a separate file; pipeline will detect this
        pasted_path = os.path.join(UPLOAD_FOLDER, "pasted_text.txt")
        with open(pasted_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        # Record that the last upload is pasted_text.txt so pipeline can pick it if requested
        write_last_upload('pasted_text.txt')
        print(f"✅ Saved pasted text: {len(text_content)} characters -> {pasted_path}")
    
    else:
        return "Invalid input mode!", 400

    # Remove previous output if exists
    try:
        if os.path.exists("Generated_Quiz.pdf"):
            os.remove("Generated_Quiz.pdf")
    except Exception:
        pass

    # Do not start processing yet; go to choose step
    return redirect(url_for("choose"))

@app.route("/start", methods=["POST"])
def start_generation():
    selected_type = request.form.get("question_type", "")
    # Start background job and show processing page
    Thread(target=_run_pipeline, args=(selected_type,), daemon=True).start()
    return redirect(url_for("processing"))

@app.route("/result")
def result():
    if not os.path.exists("Generated_Quiz.pdf"):
        return "Quiz generation failed!"
    return render_template("result.html")

@app.route("/choose")
def choose():
    return render_template("choose.html")

@app.route("/processing")
def processing():
    return render_template("processing.html")

@app.route("/status")
def status():
    ready = os.path.exists("Generated_Quiz.pdf")
    return jsonify({"ready": ready})

@app.route("/download")
def download():
    return send_file("Generated_Quiz.pdf", as_attachment=True)

@app.route("/view_pdf")
def view_pdf():
    # Serve the most recently uploaded PDF (as recorded).
    last = read_last_upload()
    if not last:
        return "No uploaded PDF available.", 404
    # If the last upload was pasted text, inform the user
    if last == 'pasted_text.txt':
        return "Latest upload is pasted text (no PDF to view).", 400

    pdf_path = os.path.join(UPLOAD_FOLDER, last)
    if os.path.exists(pdf_path):
        # Prevent caching by setting appropriate headers if needed (send_file will handle)
        return send_file(pdf_path, mimetype='application/pdf')
    return "PDF not found", 404

@app.route("/view_generated")
def view_generated():
    if os.path.exists("Generated_Quiz.pdf"):
        return send_file("Generated_Quiz.pdf", mimetype='application/pdf')
    return "Generated quiz not found", 404


if __name__ == "__main__":
    app.run(debug=True)
