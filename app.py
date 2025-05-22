from flask import Flask, request, render_template, send_from_directory
import cv2
import numpy as np
import os
import base64
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def analyze_urine_color(image_path):
    img = cv2.imread(image_path)
    img = cv2.resize(img, (200, 200))
    avg_color_per_row = np.average(img, axis=0)
    avg_color = np.average(avg_color_per_row, axis=0)
    b, g, r = avg_color
    hsv_img = cv2.cvtColor(np.uint8([[avg_color]]), cv2.COLOR_BGR2HSV)[0][0]
    h, s, v = hsv_img

    if v > 220 and s < 30:
        return "ใส (อาจดื่มน้ำมาก)"
    elif 40 < h < 70 and s > 100:
        return "เหลืองอ่อน (ปกติ)"
    elif 20 < h < 40:
        return "เหลืองเข้ม (อาจขาดน้ำ)"
    elif 10 < h < 20:
        return "ส้ม (ขาดน้ำมาก)"
    elif h < 10:
        return "น้ำตาล (ควรพบแพทย์)"
    else:
        return "ไม่สามารถประเมินได้"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' in request.files:
        file = request.files['image']
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
    else:
        data_url = request.form['camera_image']
        header, encoded = data_url.split(",", 1)
        binary_data = base64.b64decode(encoded)
        filename = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        with open(filepath, "wb") as f:
            f.write(binary_data)

    result = analyze_urine_color(filepath)
    return render_template('result.html', image_url=f'/uploads/{filename}', result=result)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18800)
