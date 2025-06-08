import numpy as np
import polars as pl
import joblib
from src.config import Config
from tqdm import tqdm


class ClassifiersApi:
	
	def __init__(self):
		self.classes = ['noisy', 'abstract', 'paint']
		self.models = dict(noisy=joblib.load(Config.noisy_model_path), abstract=joblib.load(Config.abstract_model_path), paint=joblib.load(Config.paint_model_path))
	
	def pp(self, embeddings, artwork_id: list[str]) -> pl.DataFrame:
		return self.predict_all(embeddings, artwork_id)
	
	def predict_all(self, embeddings: np.ndarray, artwork_id: list[str]):
		results = np.empty((len(embeddings), len(self.classes)))
		for i, j in tqdm(enumerate(self.classes), desc="Predicting classes"):
			results[:, i] = self.models[j].predict(embeddings).reshape(-1)
		df = pl.DataFrame({"artwork_id": artwork_id, **{self.classes[i]: results[:, i] for i in range(len(self.classes))}})
		# df.write_csv(self.csv_name)
		return df
	
	def predict_batch(self, embeddings):
		results = np.empty((len(embeddings), len(self.classes)))
		for i, j in enumerate(self.classes):
			results[:, i] = self.models[j].predict(embeddings).reshape(-1)
		return results
	
	def predict_from_embedding(self, embedding: list[float]) -> dict:
		embedding_np = np.array(embedding).reshape(1, -1)
		predictions = {cls: int(self.models[cls].predict(embedding_np)[0]) for cls in self.classes}
		return predictions

