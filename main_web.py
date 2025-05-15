from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from src.logic import Logic
from typing import List
import os
from tqdm import tqdm

class Predict(BaseModel):
    image_ids: list[int]
    target: list[int]

class ImageInfo(BaseModel):
    path: str
    name: str
    id: int

app = FastAPI()
main = Logic()
IMAGE_FOLDER = r'data\data'  # Adjust this to the actual path of your image folder

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development), use specific origins in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

def get_image_list():
    images = []
    valid_ext = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    print(f"Checking for images in: {IMAGE_FOLDER}")
    for fname in tqdm(os.listdir(IMAGE_FOLDER), desc="load images"):
        if fname.lower().endswith(valid_ext):
            try:
                img_id = int(''.join(filter(str.isdigit, fname)))
                image_path = f"/images/{fname}"  # Construct the path for serving
                images.append(ImageInfo(path=image_path, name=fname, id=img_id))
            except ValueError:
                continue
    images.sort(key=lambda x: x.id)
    return images

@app.get('/api/images')
async def list_images():
    """Returns a list of image information for the gallery."""
    return JSONResponse([img.dict() for img in get_image_list()])

@app.get('/images/{filename}')
async def get_image(filename: str):
    """Serves the actual image file."""
    print("get images")
    file_path = os.path.join(IMAGE_FOLDER, filename)
    if os.path.exists(file_path):
        from fastapi.responses import FileResponse
        return FileResponse(file_path)
    else:
        return JSONResponse({"error": "Image not found"}, status_code=404)

@app.post('/predict')
async def predict(data: Predict) -> List[int]:
    """Receives image ratings and returns a list of predicted image IDs."""
    sorted_ids, _, _ = main.predict(image_ids=data.image_ids, target=data.target)
    return sorted_ids[:10]

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)