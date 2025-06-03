import uvicorn
from fastapi import FastAPI
from typing import List
import csv
import os
from models import Artwork, UserInteraction, ArtworkResponse
from src.logic import Logic

app = FastAPI()
main = Logic(True)

# CSV persistence path
INTERACTIONS_CSV = "data/interactions.csv"

# In-memory store (replace with DB in real implementation)
interactions_db = {}

def load_interactions():
    if os.path.exists(INTERACTIONS_CSV):
        with open(INTERACTIONS_CSV, newline='', mode='r') as csvfile:
            reader = csv.reader(csvfile)
            for user_id, artwork_id, action in reader:
                if user_id not in interactions_db:
                    interactions_db[user_id] = []
                interactions_db[user_id].append((artwork_id, action))

def save_interaction(user_id: str, artwork_id: str, action: str):
    with open(INTERACTIONS_CSV, mode='a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([user_id, artwork_id, action])

# Load interactions on startup
load_interactions()

@app.post("/add-artwork", status_code=200)
def add_artwork(artwork: Artwork):
    if main.add_artwork(artwork):
        return 200
    return 400

@app.post("/user-interaction", response_model=List[ArtworkResponse])
def user_interaction(interaction: UserInteraction):
    user_id = interaction.user_id
    artwork_id = interaction.artwork_id
    action = interaction.action

    # Initialize user entry if not present
    if user_id not in interactions_db:
        interactions_db[user_id] = []

    # Check if this interaction already exists
    if (artwork_id, action) not in interactions_db[user_id]:
        interactions_db[user_id].append((artwork_id, action))
        save_interaction(user_id, artwork_id, action)  # Save only if new

    # Predict recommendations
    sorted_ids, _, _ = main.predict(
        artwork_id=[art_id for art_id, _ in interactions_db[user_id]],
        target=[1 if act == 'like' else 0 for _, act in interactions_db[user_id]],
        session_id=""
    )
    print(interactions_db)
    return [ArtworkResponse(artwork_id=id) for id in sorted_ids[:10]]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)