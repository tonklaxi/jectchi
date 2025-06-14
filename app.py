from flask import Flask, request, render_template, send_from_directory, redirect, url_for
import cv2
import numpy as np
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def analyze_urine_color(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"File not found: {image_path}")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image file: {image_path}")

    h, w, _ = img.shape
    crop_size = 150
    x1, y1 = max(w//2 - crop_size//2, 0), max(h//2 - crop_size//2, 0)
    x2, y2 = x1 + crop_size, y1 + crop_size
    roi = img[y1:y2, x1:x2]
    roi = cv2.resize(roi, (200, 200))

    avg_color = cv2.mean(roi)[:3]  # (B, G, R)
    b, g, r = avg_color

    rgb = (int(r), int(g), int(b))  # แปลงให้เป็น int เพื่อโชว์สวยงาม

    if r > 200 and g > 200 and b > 200:
        result = "ใส (อาจดื่มน้ำมาก)"
    elif r > 200 and 150 < g < 200 and b < 100:
        result = "เหลืองอ่อน (ปกติ)"
    elif r > 180 and 100 < g <= 150 and b < 80:
        result = "เหลืองเข้ม (อาจขาดน้ำ)"
    elif r > 150 and 50 < g <= 100 and b < 60:
        result = "ส้ม (ขาดน้ำมาก)"
    elif r > 100 and g < 70 and b < 50:
        result = "น้ำตาล (ควรพบแพทย์)"
    else:
        result = "ไม่สามารถประเมินได้"

    return result, rgb[0], rgb[1], rgb[2]  # return r, g, b

def analyze_nitrite_level(image_path, mode="yellow"):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"File not found: {image_path}")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image file: {image_path}")

    img = cv2.resize(img, (200, 200))

    # Crop ตรงกลางภาพ 80x80 px
    h, w, _ = img.shape
    x1, y1 = w//2 - 40, h//2 - 40
    x2, y2 = w//2 + 40, h//2 + 40
    roi = img[y1:y2, x1:x2]

    _, g, _ = cv2.mean(roi)[:3]

    if mode == "white":
        PCON = g - 248.63
        CON = abs(PCON / 35.433)
    else:  # yellow
        PCON = g - 208.23
        CON = abs(PCON / 77.37)

    CON = max(CON - 0.1, 0)

    return f"ปริมาณไนไตรต์: {CON:.2f} mg/mL"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return "ไม่พบไฟล์รูปภาพ", 400

    file = request.files['image']
    if file.filename == '':
        return "ไม่ได้เลือกไฟล์", 400

    filename = secure_filename(file.filename)
    filename = datetime.now().strftime('%Y%m%d_%H%M%S_') + filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        mode = request.form.get("mode", "yellow")
        urine_result, r, g, b = analyze_urine_color(filepath)
        nitrite_result = analyze_nitrite_level(filepath, mode)
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการประมวลผลภาพ: {e}", 500

    return render_template('result.html',
                           image_url=url_for('uploaded_file', filename=filename),
                           urine_result=urine_result,
                           nitrite_result=nitrite_result,
                           r=r, g=g, b=b)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18800, debug=True)
