from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict
import os
from tqdm import tqdm
import uvicorn
import uuid

from src.logic import Logic

# --- Constants ---
IMAGE_FOLDER = os.path.join("data", "data")  # Adjust to your actual image folder path
VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')

# --- Data Models ---
class Predict(BaseModel):
    image_ids: List[int]
    target: List[int]
    embedding: float
    color: float
    abstract: float
    noisy: float
    paint: float

class ImageInfo(BaseModel):
    path: str
    name: str
    id: int

class PredictionFidback(BaseModel):
    prediction_session_id: str
    feedback: Dict[int, int]  # image_id: rating (1 for like, 0 for dislike)

# --- App Setup ---
app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
templates = Jinja2Templates(directory="templates")
main = Logic()

active_predictions_sessions: Dict[str, List[int]] = {}

# --- CORS (for development, adjust in production) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    """Serve the main HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/images")
async def list_images():
    """List available images with metadata."""
    images = []
    count = 0
    for fname in tqdm(os.listdir(IMAGE_FOLDER), desc="Loading images"):
        if fname.lower().endswith(VALID_EXTENSIONS):
            try:
                img_id = int("".join(filter(str.isdigit, fname)))
                image_path = f"/images/{fname}"
                images.append(ImageInfo(path=image_path, name=fname, id=img_id))
                count += 1
                # if count >= 10:  # Limit to 100 images
                #     break
            except ValueError:
                continue
    images.sort(key=lambda x: x.id)
    return JSONResponse([img.dict() for img in images])

@app.get("/images/{filename}")
async def get_image(filename: str):
    """Serve an image file."""
    file_path = os.path.join(IMAGE_FOLDER, filename)
    if os.path.exists(file_path):
        response = FileResponse(file_path)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return JSONResponse({"error": "Image not found"}, status_code=404)

@app.post("/predict")
async def predict(data: Predict) -> List[int]:
    """Receive image ratings and return predicted image IDs."""
    print("Received data:", data)
    # Generate a unique session ID for the prediction
    session_id = str(uuid.uuid4())
    sorted_ids, _, _ = main.predict(
        image_ids=data.image_ids,
        target=data.target,
        session_id=session_id,
        embedding_weight=data.embedding,
        color_weight=data.color,
        abstract_weight=data.abstract,
        noisy_weight=data.noisy,
        paint_weight=data.paint
    )
    predict_top_10 = sorted_ids[:10]

    active_predictions_sessions[session_id] = {
        'weight': {
            'embedding': data.embedding,
            'color': data.color,
            'abstract': data.abstract,
            'noisy': data.noisy,
            'paint': data.paint
        },
        'liked': [id for id , label in zip(data.image_ids, data.target) if label == 1],
        'disliked': [id for id , label in zip(data.image_ids, data.target) if label == 0],
        'predicted': predict_top_10
    }
    print(f"Session ID: {session_id}, Predictions: {predict_top_10}")

    return JSONResponse({
        "session_id": session_id,
        "predicted_ids": predict_top_10
    })

@app.post("/feedback")
async def receive_feedback(data: PredictionFidback):
    """Receive feedback on predictions."""
    session_id = data.prediction_session_id
    feedback = data.feedback

    if session_id not in active_predictions_sessions:
        return JSONResponse({"error": "Invalid session ID"}, status_code=400)

    session_info = active_predictions_sessions[session_id]
    weights = session_info['weight']
    predicted_ids_for_session = session_info['predicted']
    liked_ids = session_info['liked']
    disliked_ids = session_info['disliked']

    # Extract feedback specific to the **predicted* images that were shown
    liked_feedback_ids = [img_id for img_id , rating in feedback.items() if rating == 1 and img_id in predicted_ids_for_session]
    disliked_feedback_ids = [img_id for img_id , rating in feedback.items() if rating == 0 and img_id in predicted_ids_for_session]

    main.log_prediction_and_feedback(session_id=session_id, weight=weights, liked_ids=liked_ids, disliked_ids=disliked_ids, top_predictions=[], feedback_liked=liked_feedback_ids, feedback_disliked=disliked_feedback_ids)
    return JSONResponse({"message": "Feedback received and saved successfully!"})

# --- Run with Uvicorn ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
