from flask import Flask, render_template, request
import serial
import serial.tools.list_ports
import time
from classify import classify_image
from imageCapture import capture_image
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
PORT = "COM7"  # Update this if needed
BAUD = 9600
# Change this to your actual Arduino serial port
ser = serial.Serial(PORT, BAUD, timeout=1)

time.sleep(2)  # Wait for Arduino to reset

@app.route('/stream', methods=['GET', 'POST'])
def my_scheduled_function():
    # Your continuous or periodic task logic here
    capture_image(1)
    return render_template("stream.html", stream_image_path="images/photo_1.jpg")

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
    "Cactus": {
        "temp": (21, 32),
        "humidity": (10, 30),
        "moisture": (10, 30),
        "light": (700, 1023)
    },
    "Fern": {
        "temp": (16, 24),
        "humidity": (60, 90),
        "moisture": (70, 90),
        "light": (300, 600)
    },
    "Orchid": {
        "temp": (18, 28),
        "humidity": (50, 70),
        "moisture": (50, 70),
        "light": (400, 700)
    },
    "Lettuce": {
        "temp": (15, 22),
        "humidity": (60, 80),
        "moisture": (60, 85),
        "light": (400, 750)
    },
    "Pepper": {
        "temp": (20, 30),
        "humidity": (40, 70),
        "moisture": (55, 75),
        "light": (600, 900)
    },
    "Strawberry": {
        "temp": (18, 26),
        "humidity": (50, 70),
        "moisture": (65, 85),
        "light": (500, 850)
    },
    "Rose": {
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
    "Sunflower": {
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
    "Snake Plant": {
        "temp": (18, 27),
        "humidity": (30, 50),
        "moisture": (20, 40),
        "light": (300, 600)
    },
    "Peace Lily": {
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

    temp = sensor_data.get("temperature")
    humidity = sensor_data.get("humidity")
    moisture = sensor_data.get("moisture")
    light = sensor_data.get("light")

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

    if moisture is not None:
        if moisture < ideal_ranges["moisture"][0]:
            suggestions.append("Water the plant.")
        elif moisture > ideal_ranges["moisture"][1]:
            suggestions.append("Reduce watering.")

    if light is not None:
        if light < ideal_ranges["light"][0]:
            suggestions.append("Move plant to a brighter spot.")
        elif light > ideal_ranges["light"][1]:
            suggestions.append("Reduce light exposure.")

    return suggestions

@app.route('/', methods=['GET', 'POST'])
def index():
    sensor_data = parse_sensor_data()

    selected_plant = request.form.get('plant_select', None)
    suggestions = []
    if selected_plant in plant_data:
        ideal = plant_data[selected_plant]
        suggestions = check_ranges(sensor_data, ideal)

    num = 2
    capture_image(num)
    try:
        message = classify_image(f"venv/static/images/photo_{num}.jpg")
    except Exception as e:
        print(f"[ERROR] Image classification failed: {e}")
        message = "Image classification failed."

    image_path = f'images/photo_{num}.jpg'  # relative to /static

    return render_template("index.html",
                        plants=plant_data.keys(),
                        selected_plant=selected_plant,
                        sensor_data=sensor_data,
                        suggestions=suggestions,
                        message=message,
                        image_path=image_path,
                        stream_image_path = "venv/static/images/photo_1.jpg")

#except serial.SerialException as e:
 #   print(f"[ERROR] Serial port issue: {e}")

    
'''
    print("My function was called!")
    num = 1
    capture_image(num)
    message = classify_image(f"bwsi-smartgarden2/venv/images/photo_{num}.jpg")

    return render_template("index.html", **data, message=message)

'''
print("Starting Flask app...")  # Debug message
if __name__ == '__main__':
    app.run(debug=True)
