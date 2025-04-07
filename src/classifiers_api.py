import numpy as np
import polars as pl
import joblib
from src.config import Config


class ClassifiersApi:
	
	def __init__(self):
		self.classes = ['noisy', 'abstract', 'paint']
		self.models = dict(noisy=joblib.load(Config.noisy_model_path), abstract=joblib.load(Config.abstract_model_path), paint=joblib.load(Config.paint_model_path))
	
	def pp(self, embeddings, image_ids: list[str]) -> pl.DataFrame:
		return self.predict_all(embeddings, image_ids)
	
	def predict_all(self, embeddings: np.ndarray, image_ids: list[str]):
		results = np.empty((len(embeddings), len(self.classes)))
		for i, j in enumerate(self.classes):
			results[:, i] = self.models[j].predict(embeddings).reshape(-1)
		df = pl.DataFrame({"image_ids": image_ids, **{self.classes[i]: results[:, i] for i in range(len(self.classes))}})
		# df.write_csv(self.csv_name)
		return df
	
	def predict_batch(self, embeddings):
		results = np.empty((len(embeddings), len(self.classes)))
		for i, j in enumerate(self.classes):
			results[:, i] = self.models[j].predict(embeddings).reshape(-1)
		return results
