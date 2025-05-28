from fastapi import FastAPI
from typing import List
from models import Artwork, UserInteraction, ArtworkResponse
from src.logic import Logic

app = FastAPI()
main = Logic(True)

# In-memory store (replace with DB in real implementation)
interactions_db = {}

@app.post("/add-artwork", status_code=200)
def add_artwork(artwork: Artwork):
    if main.add_artwork(artwork):
        return 200
    return 400

@app.post("/user-interaction", response_model=List[ArtworkResponse])
def user_interaction(interaction: UserInteraction):
    if interaction.user_id not in interactions_db:
        interactions_db[interaction.user_id] = [(interaction.artwork_id, interaction.action)]
    else:
        interactions_db[interaction.user_id].append((interaction.artwork_id, interaction.action))
    sorted_ids, _, _ = main.predict(
        artwork_id=[artwork_id for artwork_id, _ in interactions_db[interaction.user_id]],
        target=[1 if action == 'like' else 0 for _, action in interactions_db[interaction.user_id]],
        session_id=""
    )
    return [ArtworkResponse(artwork_id=id) for id in sorted_ids[:10]]
