from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from src.logic import Logic
from typing import List


class Predict(BaseModel):
	artwork_id: list[int]
	target: list[int]


app = FastAPI()
main = Logic()

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],  # Allow all origins (for development), use specific origins in production
	allow_credentials=True, allow_methods=["*"],  # Allow all HTTP methods
	allow_headers=["*"],  # Allow all headers
)


@app.post('/predict')
def predict(data: Predict) -> List[int]:
	print(data)
	sorted_ids, _, _ = main.predict(artwork_id=data.artwork_id, target=data.target)
	return sorted_ids[:10]


if __name__ == '__main__':
	uvicorn.run(app)
