
import os
import cv2
import re
import json
from paddleocr import PaddleOCR


ocr = PaddleOCR(lang='en')


IMAGE_FOLDER = r"C:\Users\91932\Documents\Image"
OUTPUT_FILE = "output.json"


def clean_text(text):
    text = text.replace('O', '0')
    text = text.replace('I', '1')
    text = text.replace('J', '1')
    return text.strip()

def extract_data(result):
    data = []
    for line in result[0]:
        box = line[0]
        text = clean_text(line[1][0])
        y = box[0][1]

        data.append({
            "text": text,
            "y": y
        })
    return data


def extract_price(data):
    full_text = " ".join([d["text"] for d in data])

    
    full_text = re.sub(r'(\d)\s*\.\s*(\d{2})', r'\1.\2', full_text)

    prices = re.findall(r'\d+\.\d{2}', full_text)

    if not prices:
        return ""

    return min(prices, key=lambda x: float(x))  


def extract_product_name(data):
    
    data_sorted = sorted(data, key=lambda x: x["y"], reverse=True)

    bottom_texts = []

    for d in data_sorted:
        text = d["text"]

        if len(text) < 4:
            continue
        if any(x in text.lower() for x in ['pcs', 'price']):
            continue

        bottom_texts.append(text)

        if len(bottom_texts) == 4:
            break

    combined = " ".join(bottom_texts[::-1])

    
    
    combined = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', combined)

    return combined


if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, "r") as f:
        try:
            existing_data = json.load(f)
        except:
            existing_data = []
else:
    existing_data = []

existing_names = {item["image_url"] for item in existing_data}


new_output = []

image_files = [f for f in os.listdir(IMAGE_FOLDER)
               if f.lower().endswith(('.jpg', '.png', '.jpeg'))]

print(image_files)

for idx, file_name in enumerate(image_files, start=1):

    if file_name in existing_names:
        print(f"Skipping (already processed): {file_name}")
        continue

    print(f"\nProcessing: {file_name}")

    path = os.path.join(IMAGE_FOLDER, file_name)
    img = cv2.imread(path)

    if img is None:
        print(" Failed to load")
        continue

    result = ocr.ocr(img)

    data = extract_data(result)

    full_text = " ".join([d["text"] for d in data])

    price = extract_price(data)
    product_name = extract_product_name(data)

    new_output.append({
        "id": len(existing_data) + len(new_output) + 1,
        "image_url": file_name,
        "extracted_text": full_text,
        "product_name": product_name,
        "price": price
    })


existing_data.extend(new_output)

with open(OUTPUT_FILE, "w") as f:
    json.dump(existing_data, f, indent=4)

print("\n Done! Data appended to output.json")