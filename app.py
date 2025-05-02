import os
import cv2
import numpy as np
from flask import Flask, request, send_from_directory, render_template_string, url_for, redirect
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# CSS_STYLE (original orange theme with slider styling)
CSS_STYLE = """
body {
    font-family: Arial, sans-serif;
    background-color: #fff7f0;
    color: #333;
    padding: 20px;
    text-align: center;
}
h1 {
    color: #FF5733;
}
form {
    background-color: #fff;
    padding: 20px;
    border-radius: 10px;
    display: inline-block;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}
input[type="file"], select, input[type="range"] {
    margin: 10px 0;
    padding: 10px;
    width: 100%;
    max-width: 300px;
}
input[type="submit"] {
    background-color: #C70039;
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
}
input[type="submit"]:hover {
    background-color: #900C3F;
}
img {
    margin: 20px;
    max-width: 90%;
    height: auto;
    border-radius: 10px;
    border: 2px solid #FF5733;
}
.slider-label {
    margin-top: 10px;
    font-weight: bold;
}
"""

# INDEX_HTML
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Image Enhancer</title>
    <style>{{ css }}</style>
</head>
<body>
    <h1>🧪 Image Histogram Equalization</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="image" required><br>
        <label for="grayscale">Convert to Grayscale?</label>
        <select name="grayscale">
            <option value="no">No</option>
            <option value="yes">Yes</option>
        </select><br>
        <div class="slider-label">Intensity:</div>
        <input type="range" min="1" max="100" value="100" name="intensity" id="intensitySlider">
        <div id="intensityValue">100%</div>
        <script>
            const slider = document.getElementById('intensitySlider');
            const output = document.getElementById('intensityValue');
            slider.oninput = function() {
                output.innerHTML = this.value + '%';
            }
        </script>
        <br><br>
        <input type="submit" value="Enhance">
    </form>
</body>
</html>
"""

# RESULT_HTML
RESULT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Result</title>
    <style>{{ css }}</style>
</head>
<body>
    <h1>✅ Result</h1>
    <h3>Original Image</h3>
    <img src="{{ url_for('uploaded_file', filename=filename) }}">
    <h3>Enhanced Image</h3>
    <img src="{{ url_for('processed_file', filename=filename) }}">
    <br><br>
    <a href="{{ url_for('download_file', filename=filename) }}">Download Image</a>
    <br><br>
    <a href="{{ url_for('index') }}">🔙 Back</a>
</body>
</html>
"""

# IMAGE PROCESSING (Histogram Equalization with Intensity Control)
def equalize_histogram(input_path, output_path, grayscale=False, intensity=1.0):
    try:
        image = cv2.imread(input_path)

        if image is None:
            raise ValueError(f"Failed to load image from {input_path}")

        if grayscale:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            equalized = cv2.equalizeHist(gray)
            equalized_bgr = cv2.cvtColor(equalized, cv2.COLOR_GRAY2BGR)
        else:
            ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
            y, cr, cb = cv2.split(ycrcb)
            y_eq = cv2.equalizeHist(y)
            y_blend = cv2.addWeighted(y, 1 - intensity, y_eq, intensity, 0)
            ycrcb_eq = cv2.merge((y_blend.astype(np.uint8), cr, cb))
            equalized_bgr = cv2.cvtColor(ycrcb_eq, cv2.COLOR_YCrCb2BGR)

        cv2.imwrite(output_path, equalized_bgr)

    except Exception as e:
        print(f"Error processing image: {str(e)}")
        if os.path.exists(input_path):
            import shutil
            shutil.copy(input_path, output_path)

# ROUTES
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'image' not in request.files:
            return redirect(request.url)

        file = request.files['image']

        if file.filename == '':
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
            file.save(input_path)

            grayscale = request.form.get('grayscale') == 'yes'
            intensity = float(request.form.get('intensity', '100')) / 100.0
            equalize_histogram(input_path, output_path, grayscale, intensity)

            return render_template_string(RESULT_HTML, filename=filename, css=CSS_STYLE)

    return render_template_string(INDEX_HTML, css=CSS_STYLE)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/processed/<filename>')
def processed_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
