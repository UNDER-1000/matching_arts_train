import numpy as np
import polars as pl
from utils.embed_model import ClipEmbed
import json
from src.config import Config
from tqdm import tqdm


class EmbeddingsApi:
	def __init__(self):
		self.images_folder = Config.images_folder
		self.batch_size: int = 16
		self.embed_dim: int = 768
		self.embed_model = ClipEmbed()
		
	def pp(self, artwork_id):
		return self.predict_all(artwork_id)
	
	def predict_batch(self, artwork_id):
		all_embeddings = []
		
		for i in tqdm(range(0, len(artwork_id), self.batch_size), desc="Predicting embeddings"):
			batch_images = artwork_id[i:i + self.batch_size]
			batch_images = [f"{self.images_folder}{img}.jpg" for img in batch_images]
			
			embeddings = self.embed_model.predict_imgs(batch_images).tolist()
			[all_embeddings.append(e) for e in embeddings]
		return np.array(all_embeddings)
	
	def predict_all(self, artwork_id) -> pl.DataFrame:
		all_embeddings = self.predict_batch(artwork_id)
		df = pl.DataFrame({"artwork_id": artwork_id, "embeddings": [json.dumps(embeddings) for embeddings in all_embeddings.tolist()]})
		# df.write_csv(self.csv_name)
		return df

	def predict_from_path(self, image_path: str) -> list[float]:
		embedding = self.embed_model.predict_imgs([image_path])[0]
		return embedding.tolist()