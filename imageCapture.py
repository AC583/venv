# capture_image.py

import requests
import os

esp32_ip = "192.168.1.170"  # change to your ESP32 IP

def capture_image(name, folder="venv/static/images"):
    os.makedirs(folder, exist_ok=True)

    output_file = os.path.join(folder, f"photo_{name}.jpg")

    url = f"http://{esp32_ip}/capture"
    response = requests.get(url)

    if response.status_code == 200:
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print(f"Image saved as {output_file}")
    else:
        print(f"Failed to capture image: {response.status_code}")



'''import cv2
import time
stream_url = 'http://192.168.1.170:81/stream'
cap = cv2.VideoCapture(stream_url)

while True:
    ret, frame = cap.read()
    if ret:
        filename = f"frame_{int(time.time())}.jpg"
        cv2.imwrite(filename, frame)
        print(f"Saved {filename}")
    else:
        print("Failed to grab frame")
    time.sleep(5)'''
