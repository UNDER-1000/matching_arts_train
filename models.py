from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class Artwork(BaseModel):
    artwork_id: str
    artist_id: str
    artist_name: str
    artwork_name: str
    images: List[str]
    description: Optional[str] = None
    category: Optional[str] = None
    media: Optional[str] = None
    medium: Optional[str] = None
    size: Optional[str] = None
    price: Optional[float] = None
    styles: Optional[List[str]] = None
    subject: Optional[str] = None

class UserInteraction(BaseModel):
    user_id: str
    artwork_id: str
    action: str
    timestamp: datetime

class ArtworkResponse(BaseModel):
    artwork_id: str
