from sqlalchemy import Column, String, Integer, JSON, Text, Float, select
from db import Base

class ArtworkDB(Base):
    __tablename__ = "artworks"

    artwork_id = Column(String, primary_key=True)
    artist_id = Column(String)
    artist_name = Column(String)
    artwork_name = Column(String)
    images = Column(JSON)
    description = Column(String)
    category = Column(String)
    properties = Column(JSON)
    embeddings = Column(JSON)
    colors = Column(JSON)
    abstract = Column(Float)
    noisy = Column(Float)
    paint = Column(Float)

class UserInteractionDB(Base):
    __tablename__ = "user_interactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    artwork_id = Column(String, nullable=False)
    action = Column(String, nullable=False)

class PredictionLog(Base):
    __tablename__ = "prediction_logs"
    session_id = Column(String, primary_key=True)
    weight = Column(JSON)
    liked_ids = Column(JSON)
    disliked_ids = Column(JSON)
    top_predictions = Column(JSON)
    feedback_liked = Column(JSON)
    feedback_disliked = Column(JSON)
