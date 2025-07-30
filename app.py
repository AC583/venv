from flask import Flask, render_template, request, redirect, url_for, session
import serial
import time
from classify import classify_image
from imageCapture import capture_image

app = Flask(__name__)
selected_plant = None

# Change this to your actual Arduino serial port
ser = serial.Serial('COM7', 9600, timeout=1)
time.sleep(2)  # Wait for Arduino to reset

# Synthetic dataset of 15 plants with ideal ranges
plant_data = {
    "Tomato": {
        "temp": (18, 27),
        "humidity": (50, 70),
        "moisture": (60, 80),
        "light": (600, 900)
    },
    "Basil": {
        "temp": (20, 30),
        "humidity": (40, 60),
        "moisture": (50, 75),
        "light": (500, 800)
    },
    "Lettuce": {
        "temp": (21, 32),
        "humidity": (10, 30),
        "moisture": (10, 30),
        "light": (700, 1023)
    },
    "Potato": {
        "temp": (16, 24),
        "humidity": (60, 90),
        "moisture": (70, 90),
        "light": (300, 600)
    },
    "Olive": {
        "temp": (18, 28),
        "humidity": (50, 70),
        "moisture": (50, 70),
        "light": (400, 700)
    },
    "Strawberry": {
        "temp": (15, 22),
        "humidity": (60, 80),
        "moisture": (60, 85),
        "light": (400, 750)
    },
    "Rose": {
        "temp": (20, 30),
        "humidity": (40, 70),
        "moisture": (55, 75),
        "light": (600, 900)
    },
    "Sunflower": {
        "temp": (18, 26),
        "humidity": (50, 70),
        "moisture": (65, 85),
        "light": (500, 850)
    },
    "Orchid": {
        "temp": (15, 25),
        "humidity": (40, 60),
        "moisture": (60, 80),
        "light": (500, 900)
    },
    "Mint": {
        "temp": (18, 28),
        "humidity": (40, 60),
        "moisture": (50, 75),
        "light": (400, 700)
    },
    "Corn": {
        "temp": (20, 30),
        "humidity": (40, 70),
        "moisture": (50, 75),
        "light": (700, 1023)
    },
    "Aloe Vera": {
        "temp": (18, 30),
        "humidity": (20, 40),
        "moisture": (10, 30),
        "light": (600, 1023)
    },
    "Lavender": {
        "temp": (15, 25),
        "humidity": (30, 50),
        "moisture": (40, 60),
        "light": (500, 900)
    },
    "Okra": {
        "temp": (18, 27),
        "humidity": (30, 50),
        "moisture": (20, 40),
        "light": (300, 600)
    },
    "Lily": {
        "temp": (18, 25),
        "humidity": (60, 80),
        "moisture": (60, 80),
        "light": (200, 500)
    }
}


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


@app.route('/stream', methods=['GET', 'POST'])
def my_scheduled_function():
    # Your continuous or periodic task logic here
    capture_image(1)
    return render_template("stream.html", stream_image_path="images/photo_1.jpg")


app.secret_key = 'some_secret_key'  # required for session

@app.route('/', methods=['GET', 'POST'])
def index():
    sensor_data = parse_sensor_data()
    if request.method == 'POST':
        selected_plant = request.form.get('plant_select', None)
        session['selected_plant'] = selected_plant
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
                           suggestions=suggestions)

@app.route('/show_output', methods=['POST'])
def show_output():
    num = 2
    capture_image(num)
    try:
        text_output = classify_image(f"venv/static/images/photo_{num}.jpg")
    except Exception as e:
        print(f"[ERROR] Image classification failed: {e}")
        text_output = "Image classification failed."

    image_path = 'images/photo_1.jpg'
    return render_template('result.html', image=image_path, text=text_output)

@app.route('/WATER', methods=['POST'])
def water_plant():
    try:
        ser.write(b'WATER\n')
        time.sleep(1)
    except Exception as e:
        print("Error sending to Arduino:", e)
    # Redirect back to index, selected_plant preserved in session
    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)

#except serial.SerialException as e:
 #   print(f"[ERROR] Serial port issue: {e}")

    
'''
    print("My function was called!")
    num = 1
    capture_image(num)
    message = classify_image(f"bwsi-smartgarden2/venv/images/photo_{num}.jpg")

    return render_template("index.html", **data, message=message)

'''