import uvicorn
from fastapi import FastAPI
from typing import List
from models import Artwork, UserInteraction, ArtworkResponse
from src.logic import Logic
from src.walls_logic import PredictionWalls
from db import connect_db, close_db, get_connection
from sqlalchemy import text, select
from models_db import UserInteractionDB, ArtworkDB

app = FastAPI()
artwork_recommender = None
walls_recommender = None

@app.on_event("startup")
async def startup():
    await connect_db()

@app.on_event("shutdown")
async def shutdown():
    await close_db()

def get_artwork_recommender() -> Logic:
    global artwork_recommender
    if artwork_recommender is None:
        artwork_recommender = Logic()  # expensive init
    return artwork_recommender

def get_walls_recommender() -> PredictionWalls:
    global walls_recommender
    if walls_recommender is None:
        walls_recommender = PredictionWalls()  # expensive init
    return walls_recommender

@app.post("/add-artwork", status_code=200)
async def add_artwork(artwork: Artwork):
    recommender = get_artwork_recommender()
    result = await recommender.add_artwork(artwork)
    return 200 if result else 400

async def record_artwork_feedback(user_id: str, artwork_id: str, action: str) -> List[str]:
    async with get_connection() as session:
        # Check if interaction already exists
        stmt = select(UserInteractionDB).where(
            UserInteractionDB.user_id == user_id,
            UserInteractionDB.artwork_id == artwork_id,
            UserInteractionDB.action == action
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        # Save new interaction if not exists
        if not existing:
            new_record = UserInteractionDB(
                user_id=user_id,
                artwork_id=artwork_id,
                action=action
            )
            session.add(new_record)
            await session.commit()

        # Fetch all interactions for this user
        stmt_all = select(UserInteractionDB).where(
            UserInteractionDB.user_id == user_id
        )
        result_all = await session.execute(stmt_all)
        interactions = result_all.scalars().all()

        # Prepare input for prediction
        artwork_ids = [i.artwork_id for i in interactions]
        targets = [1 if i.action == "like" else 0 for i in interactions]

        recommender = get_artwork_recommender()
        sorted_ids = await recommender.predict(
            artwork_id=artwork_ids,
            target=targets
        )

    return [id for id in sorted_ids]

@app.delete("/delete-artwork/{artwork_id}", status_code=200)
async def delete_artwork(artwork_id: str):
    async with get_connection() as session:
        stmt = select(ArtworkDB).where(ArtworkDB.artwork_id == artwork_id)
        result = await session.execute(stmt)
        artwork = result.scalar_one_or_none()

        if not artwork:
            return {"status": "not found"}

        await session.delete(artwork)
        await session.commit()
        return {"status": "deleted", "artwork_id": artwork_id}
    
@app.delete("/delete-by-artist/{artist_id}", status_code=200)
async def delete_by_artist(artist_id: str):
    async with get_connection() as session:
        stmt = select(ArtworkDB).where(ArtworkDB.artist_id == artist_id)
        result = await session.execute(stmt)
        artworks = result.scalars().all()

        if not artworks:
            return {"status": "not found"}

        for artwork in artworks:
            await session.delete(artwork)

        await session.commit()
        return {
            "status": "deleted",
            "artist_id": artist_id,
            "count": len(artworks)
        }

@app.post("/user-interaction", response_model=List[str])
async def user_interaction(interaction: UserInteraction):
    user_id = interaction.user_id
    artwork_id = interaction.artwork_id
    action = interaction.action

    if action == "like" or action == "dislike":
        return await record_artwork_feedback(user_id, artwork_id, action)
    elif action == "wall":
        recommender = get_walls_recommender()
        return recommender.predict(artwork_id, k=10)[0]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)