from sqlalchemy import Column, String, Integer, JSON, Text, Float
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

class WallSelectionDB(Base):
    __tablename__ = "wall_selections"
    wall_index = Column(Text, primary_key=True)
    selected_artworks = Column(JSON)
