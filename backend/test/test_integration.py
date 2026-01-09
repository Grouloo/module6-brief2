import requests
import numpy as np
from PIL import Image
import io

API_URL = "http://localhost:8000"

def create_dummy_image():
    # Create a 28x28 black image with a white line
    img = Image.new('L', (28, 28), color=0)
    for i in range(5, 25):
        img.putpixel((i, i), 255)
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    return img_bytes.getvalue()

def test_predict():
    print("Testing /predict...")
    img_bytes = create_dummy_image()
    files = {"file": ("test_image.png", img_bytes, "image/png")}
    
    try:
        response = requests.post(f"{API_URL}/predict", files=files)
        if response.status_code == 200:
            print("Prediction Success:", response.json())
            return response.json().get("prediction")
        else:
            print("Prediction Failed:", response.text)
            return None
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def test_correct(predicted_label):
    if predicted_label is None:
        print("Skipping correction test due to prediction failure.")
        return

    print("Testing /correct...")
    img_bytes = create_dummy_image()
    files = {"file": ("test_image.png", img_bytes, "image/png")}
    data = {
        "true_label": 1, # Let's say it was a 1
        "predicted_label": predicted_label
    }
    
    try:
        response = requests.post(f"{API_URL}/correct", files=files, data=data)
        if response.status_code == 200:
            print("Correction Success:", response.json())
        else:
            print("Correction Failed:", response.text)
    except Exception as e:
         print(f"Connection failed: {e}")

if __name__ == "__main__":
    print(f"Checking API at {API_URL}")
    pred = test_predict()
    test_correct(pred)
