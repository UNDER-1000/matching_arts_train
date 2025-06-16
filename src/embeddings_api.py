import numpy as np
import polars as pl
from utils.embed_model import ClipEmbed
import json
from src.config import Config
from tqdm import tqdm


class EmbeddingsApi:
	def __init__(self):
		self.batch_size: int = 16
		self.embed_dim: int = 768
		self.embed_model = ClipEmbed()
	
	def predict_from_path(self, image_path: str) -> list[float]:
		embedding = self.embed_model.predict_imgs([image_path])[0]
		return embedding.tolist()