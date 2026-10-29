import os
import requests
from dotenv import load_dotenv

load_dotenv()

PICTURES_URL = os.environ["PICTURES_URL"]
SOURCE_DIR = "DroneCaptures/29.10.2026" 

def upload_real_photos(directory_path: str, plant_id: int):
    """Scans a directory for real images and uploads them sequentially."""
    if not os.path.exists(directory_path):
        print(f"Error: Folder '{directory_path}' not found.")
        return

    valid_extensions = (".jpg", ".jpeg", ".png")
    image_files = [f for f in os.listdir(directory_path) if f.lower().endswith(valid_extensions)]
    
    if not image_files:
        print(f"No valid images found in '{directory_path}'.")
        return

    print(f"Found {len(image_files)} images. Starting upload sequence...\n")

    for filename in image_files:
        image_path = os.path.join(directory_path, filename)
        
        # Determine content type based on extension
        content_type = "image/png" if filename.lower().endswith(".png") else "image/jpeg"

        with open(image_path, "rb") as img:
            files = {"file": (filename, img, content_type)}
            
            data = {
                "plant_id": plant_id,
                "flight_id": 1  # For example, Flight Session #1
            }

            print(f"Uploading {filename} (Plant #{plant_id}, Flight #{data['flight_id']})...")
            try:
                response = requests.post(PICTURES_URL, files=files, data=data)
                if response.status_code == 200:
                    print(f"  -> Success! Stored at: {response.json()['url']}")
                else:
                    print(f"  -> Failed [Status {response.status_code}]: {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"  -> Connection Error: {e}")

if __name__ == "__main__":
    # You can change the plant_id here to map these photos to a different plant in the dashboard
    upload_real_photos(SOURCE_DIR, plant_id=1)
