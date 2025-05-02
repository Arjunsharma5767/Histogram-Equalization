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

# CSS STYLE
CSS_STYLE = """
body {
    font-family: 'Segoe UI', sans-serif;
    background: #fefefe;
    color: #333;
    margin: 0;
    padding: 0;
    text-align: center;
}
.container {
    max-width: 800px;
    margin: auto;
    padding: 20px;
}
h1 {
    color: #FF5733;
}
form {
    background: #fff;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.1);
}
input[type="file"], select {
    margin: 10px 0;
    padding: 10px;
}
input[type="submit"] {
    padding: 10px 20px;
    background-color: #C70039;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
}
input[type="submit"]:hover {
    background-color: #900C3F;
}
.image-container {
    display: flex;
    justify-content: space-around;
    flex-wrap: wrap;
    margin-top: 20px;
}
img {
    max-width: 100%;
    height: auto;
    border: 1px solid #ddd;
    border-radius: 5px;
    margin: 10px;
}
a.button {
    display: inline-block;
    padding: 10px 20px;
    background-color: #FF5733;
    color: white;
    text-decoration: none;
    border-radius: 5px;
    margin-top: 20px;
}
a.button:hover {
    background-color: #C70039;
}
"""

# HTML Templates

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Image Enhancer - Histogram Equalization</title>
    <style>{{ css }}</style>
</head>
<body>
    <div class="container">
        <h1>📸 Image Enhancer</h1>
        <form method="post" enctype="multipart/form-data">
            <p><strong>Select an image to enhance:</strong></p>
            <input type="file" name="image" required><br>
            <label for="grayscale">Convert to Grayscale before Equalizing?</label>
            <select name="grayscale">
                <option value="no">No</option>
                <option value="yes">Yes</option>
            </select><br>
            <input type="submit" value="Enhance Image">
        </form>
    </div>
</body>
</html>
"""

RESULT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced Image</title>
    <style>{{ css }}</style>
</head>
<body>
    <div class="container">
        <h1>✨ Enhancement Complete!</h1>
        <div class="image-container">
            <div>
                <h3>Original Image</h3>
                <img src="{{ url_for('uploaded_file', filename=filename) }}">
            </div>
            <div>
                <h3>Enhanced Image</h3>
                <img src="{{ url_for('processed_file', filename=filename) }}">
            </div>
        </div>
        <a class="button" href="{{ url_for('download_file', filename=filename) }}">⬇️ Download Enhanced Image</a>
        <br><br>
        <a class="button" href="{{ url_for('index') }}">🔄 Enhance Another</a>
    </div>
</body>
</html>
"""

# IMAGE PROCESSING FUNCTION
def equalize_histogram(input_path, output_path, grayscale=False):
    """
    Apply histogram equalization to the image

    Parameters:
    - input_path: Path to the input image
    - output_path: Path to save the processed image
    - grayscale: Whether to convert to grayscale before equalization
    """
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
            ycrcb_eq = cv2.merge((y_eq, cr, cb))
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
            equalize_histogram(input_path, output_path, grayscale)

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
