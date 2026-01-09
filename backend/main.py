from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from loguru import logger
from sys import stderr
import os
import aiofiles
from modules.model import mnist_model
from modules.db import init_db, save_correction

app = FastAPI()

logger.add(stderr, format="{time} {level} {message}", filter="my_module", level="INFO")
logger.add("logs/api.log")

@app.on_event("startup")
def startup_event():
    init_db()
    logger.info("API started.")

@app.get("/")
async def homepage():
    return {"message": "Digit Recognition API"}

@app.post("/predict")
async def predict_digit_endpoint(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        prediction, probs = mnist_model.predict(contents)
        logger.info(f"Prediction: {prediction}")
        return {"prediction": prediction, "probabilities": probs}
    except Exception as e:
        logger.error(f"Error during prediction: {e}")
        return {"error": str(e)}

@app.post("/correct")
async def correct_prediction(
    file: UploadFile = File(...),
    true_label: int = Form(...),
    predicted_label: int = Form(...)
):
    try:
        # Save image for retraining
        filename = f"correction_{true_label}_{predicted_label}_{os.urandom(4).hex()}.png"
        file_path = f"/app/data/corrections/{filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
            
        save_correction(file_path, true_label, predicted_label)
        return {"status": "success", "message": "Correction saved"}
    except Exception as e:
        logger.error(f"Error saving correction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reload")
async def reload_model():
    try:
        mnist_model.reload()
        return {"status": "success", "message": "Model reloaded"}
    except Exception as e:
        logger.error(f"Error reloading model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/health')
async def health():
    return { "status": "ok" }