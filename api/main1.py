from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import numpy as np
from io import BytesIO
from PIL import Image
import tensorflow as tf
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import logging

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

MODEL = tf.keras.models.load_model("saved_model1.keras")

CLASS_NAMES = ["Early Blight", "Healthy", "Late Blight"]

@app.get("/ping")
async def ping():
    return {"message": "Hello, I am alive"}

def read_file_as_image(data) -> np.ndarray:
    image = np.array(Image.open(BytesIO(data)))
    return image

@app.post("/predict", response_class=HTMLResponse)
async def predict(request: Request, file: UploadFile = File(...)):
    try:
        logging.info("Received file: %s", file.filename)
        image = read_file_as_image(await file.read())
        img_batch = np.expand_dims(image, 0)
        prediction = MODEL.predict(img_batch)
        predicted_class = CLASS_NAMES[np.argmax(prediction[0])]
        confidence = np.max(prediction[0]) * 100
        logging.info("Prediction: %s, Confidence: %.2f%%", predicted_class, confidence)
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "predicted_class": predicted_class, 
            "confidence": confidence
        })
    except Exception as e:
        logging.error("Error during prediction: %s", str(e))
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "predicted_class": "Error",
            "confidence": 0
        })

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host='127.0.0.1', port=8000)
