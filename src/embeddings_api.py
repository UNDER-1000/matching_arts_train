import numpy as np
import polars as pl
from utils.embed_model import ClipEmbed
import json
from src.config import Config


class EmbeddingsApi:
	def __init__(self):
		self.images_folder = Config.images_folder
		self.batch_size: int = 16
		self.embed_dim: int = 768
		self.embed_model = ClipEmbed()
		
	def pp(self, image_ids):
		return self.predict_all(image_ids)
	
	def predict_batch(self, image_ids):
		all_embeddings = []
		
		for i in range(0, len(image_ids), self.batch_size):
			batch_images = image_ids[i:i + self.batch_size]
			batch_images = [f"{self.images_folder}{img}.jpg" for img in batch_images]
			
			embeddings = self.embed_model.predict_imgs(batch_images).tolist()
			[all_embeddings.append(e) for e in embeddings]
		return np.array(all_embeddings)
	
	def predict_all(self, image_ids) -> pl.DataFrame:
		all_embeddings = self.predict_batch(image_ids)
		df = pl.DataFrame({"image_ids": image_ids, "embeddings": [json.dumps(embeddings) for embeddings in all_embeddings.tolist()]})
		# df.write_csv(self.csv_name)
		return df
		