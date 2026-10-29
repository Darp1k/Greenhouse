import os
import uuid
import aiofiles
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# Import database setup and models
from database import engine, get_db, Base
import models

# Automatically generate tables in MySQL if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Marble 2.0 Ingestion Gateway")

UPLOAD_DIR = "static/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/images", StaticFiles(directory=UPLOAD_DIR), name="images")

# post endpoint to handle drone image uploads
@app.post("/api/v1/upload")
async def upload_drone_capture(
    plant_id: int = Form(...),
    flight_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db) # connect the database session for this request
):
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=415, detail="Unsupported media type")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing")

    # Generate unique filename
    extension = file.filename.split('.')[-1]
    unique_id = uuid.uuid4().hex[:8]
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"plant_{plant_id}_{timestamp_str}_{unique_id}.{extension}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    # Save to disk
    async with aiofiles.open(file_path, 'wb') as out_file:
        while chunk := await file.read(1024 * 1024): 
            await out_file.write(chunk)

    # database transaction start
    
    # 1. Ensure the plant exists
    plant_record = db.query(models.Plant).filter(models.Plant.plant_index == plant_id).first()
    if not plant_record:
        plant_record = models.Plant(plant_index=plant_id)
        db.add(plant_record)
        db.commit()
        db.refresh(plant_record)

    # 2. Ensure the flight exists
    flight_record = db.query(models.Flight).filter(models.Flight.id == flight_id).first()
    if not flight_record:
        flight_record = models.Flight(id=flight_id)
        db.add(flight_record)
        db.commit()
        db.refresh(flight_record)

    # 3. Record the image capture
    new_capture = models.Capture(
        plant_id=plant_record.id,
        flight_id=flight_record.id,
        file_path=f"/images/{safe_filename}"
    )
    db.add(new_capture)
    db.commit()
    
    return {
        "status": "success", 
        "url": new_capture.file_path,
        "plant_id": plant_id
    }

# get endpoint to fetch all captures for a specific plant
@app.get("/api/v1/captures/{plant_index}")
def get_plant_captures(plant_index: int, db: Session = Depends(get_db)):
    """Fetches all image paths and flight data for a specific plant."""
    # Find the plant in the database
    plant = db.query(models.Plant).filter(models.Plant.plant_index == plant_index).first()
    
    if not plant:
        return {"status": "error", "captures": []}
        
    # Retrieve all captures for this plant, ordered by newest first
    captures = (
        db.query(models.Capture)
        .filter(models.Capture.plant_id == plant.id)
        .order_by(models.Capture.timestamp.desc())
        .all()
    )
    
    # Return the data as JSON for the Dash frontend
    return {
        "status": "success", 
        "plant_index": plant_index,
        "captures": [
            {
                "file_path": c.file_path, 
                "flight_id": c.flight_id, 
                "timestamp": c.timestamp.isoformat()
            } for c in captures
        ]
    }
