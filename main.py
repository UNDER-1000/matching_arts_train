import uvicorn
from fastapi import FastAPI
from typing import List
from models import Artwork, UserInteraction, ArtworkResponse
from src.logic import Logic
from src.walls_logic import PredictionWalls
from db import connect_db, close_db, get_connection
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from models_db import UserInteractionDB, WallSelectionDB

app = FastAPI()
artwork_recommender = Logic()
walls_recommender = PredictionWalls()

@app.on_event("startup")
async def startup():
    await connect_db()

@app.on_event("shutdown")
async def shutdown():
    await close_db()

@app.post("/add-artwork", status_code=200)
async def add_artwork(artwork: Artwork):
    result = await artwork_recommender.add_artwork(artwork)
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

        sorted_ids = await artwork_recommender.predict(
            artwork_id=artwork_ids,
            target=targets
        )

    return [id for id in sorted_ids]

@app.post("/user-interaction", response_model=List[str])
async def user_interaction(interaction: UserInteraction):
    user_id = interaction.user_id
    artwork_id = interaction.artwork_id
    action = interaction.action

    if action == "like" or action == "dislike":
        return await record_artwork_feedback(user_id, artwork_id, action)
    elif action == "wall":
        return walls_recommender.predict(artwork_id, k=10)[0]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)