from flask import Flask, render_template, request, redirect, url_for, session, Response
import serial
import time
import os
import cv2
from classify import classify_image
from imageCapture import capture_image
import plantdata
import requests
import threading

app = Flask(__name__)
selected_plant = None
text = None
classify_image_path = None
plant_data = plantdata.plant_data  # Load the plant data

# Change this to your actual Arduino serial port
ser = serial.Serial('COM7', 9600, timeout=1)
time.sleep(2)  # Wait for Arduino to reset

# === CONFIGURATION ===
ESP32_URL = "http://192.168.1.170/capture"  # Replace with your ESP32 URL
SAVE_PATH = "venv/static/images/photo_2.jpg"

# === IMAGE FETCHING THREAD ===
def fetch_from_esp32():
    while True:
        try:
            capture_image(2)  # or your chosen path
        except Exception as e:
            print("[ERROR] Failed to fetch image:", e)
        time.sleep(0.1)  # ~10 fps

# === STREAMING FUNCTION ===
def generate_frames():
    image_path = "venv/static/images/photo_2.jpg"  # <- match with capture path

    while True:
        if os.path.exists(image_path):
            frame = cv2.imread(image_path)
            if frame is not None:
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    frame = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.1)

# === VIDEO FEED ROUTE ===
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')



def parse_sensor_data():
    """
    Read serial lines and parse sensor data.
    Expected lines: Temperature, Humidity, Moisture, Light, Hour
    """
    data = {
        "temperature": None,
        "humidity": None,
        "moisture": None,
        "light": None,
        "hour": None
    }

    lines_read = 0
    start_time = time.time()
    while lines_read < 10 and (time.time() - start_time < 5):
        if ser.in_waiting:
            line = ser.readline().decode(errors='ignore').strip()
            lines_read += 1
            if "Temperature" in line:
                try:
                    data["temperature"] = float(line.split(":")[1].strip())
                except:
                    pass
            elif "Humidity" in line:
                try:
                    data["humidity"] = float(line.split(":")[1].strip())
                except:
                    pass
            elif "Moisture" in line:
                try:
                    # Expected format: e.g. 85% - strip %
                    val = line.split(":")[1].strip().replace('%','')
                    data["moisture"] = float(val)
                except:
                    pass
            elif "Light" in line:
                try:
                    data["light"] = int(line.split(":")[1].strip())
                except:
                    pass
            elif "Hour" in line:
                try:
                    data["hour"] = int(line.split(":")[1].strip())
                except:
                    pass
    return data


def check_ranges(sensor_data, ideal_ranges):
    suggestions = []
    
    moisture = sensor_data.get("moisture")
    temp = sensor_data.get("temperature")
    humidity = sensor_data.get("humidity")
    light = sensor_data.get("light")

    if moisture is not None:
        if moisture < ideal_ranges["moisture"][0]:
            suggestions.append("Increase watering.")
        elif moisture > ideal_ranges["moisture"][1]:
            suggestions.append("Reduce watering.")
           
    if temp is not None:
        if temp < ideal_ranges["temp"][0]:
            suggestions.append("Increase temperature.")
        elif temp > ideal_ranges["temp"][1]:
            suggestions.append("Decrease temperature.")

    if humidity is not None:
        if humidity < ideal_ranges["humidity"][0]:
            suggestions.append("Increase humidity.")
        elif humidity > ideal_ranges["humidity"][1]:
            suggestions.append("Decrease humidity.")


    if light is not None:
        if light < ideal_ranges["light"][0]:
            suggestions.append("Move plant to a brighter spot.")
        elif light > ideal_ranges["light"][1]:
            suggestions.append("Reduce light exposure.")

    return suggestions

app.secret_key = 'some_secret_key'  # required for session

@app.route('/', methods=['GET', 'POST'])
def index():
    sensor_data = parse_sensor_data()
    text= None
    classify_image_path = None

    if request.method == 'POST':
        button_clicked = request.form.get('button')
        print(f"[INFO] Button clicked: {button_clicked}")
        selected_plant = request.form.get('plant_select', None)
        session['selected_plant'] = selected_plant

        if button_clicked == 'classify':
            num = 1
            capture_image(num)
            try:
                text = classify_image(f"venv/static/images/photo_{num}.jpg")
                print(f"[INFO] Classification result: {text}")
            except Exception as e:
                print(f"[ERROR] Image classification failed: {e}")
                text = "Image classification failed."
            classify_image_path = 'images/photo_1.jpg'

    else:
        selected_plant = session.get('selected_plant', None)

    suggestions = []
    if selected_plant in plant_data:
        ideal = plant_data[selected_plant]
        suggestions = check_ranges(sensor_data, ideal)

    return render_template("index.html",
                           plants=plant_data.keys(),
                           selected_plant=selected_plant,
                           sensor_data=sensor_data,
                           suggestions=suggestions,
                           text=text,
                           classify_image_path=classify_image_path)

@app.route('/WATER', methods=['POST'])
def water_plant():
    try:
        ser.write(b'WATER\n')
        time.sleep(1)
    except Exception as e:
        print("Error sending to Arduino:", e)
    # Redirect back to index, selected_plant preserved in session
    return redirect(url_for('index'))


# === MAIN ===
if __name__ == '__main__':
    t = threading.Thread(target=fetch_from_esp32)
    t.daemon = True
    t.start()

    app.run(host='0.0.0.0', port=5000, debug=True)


#except serial.SerialException as e:
 #   print(f"[ERROR] Serial port issue: {e}")


