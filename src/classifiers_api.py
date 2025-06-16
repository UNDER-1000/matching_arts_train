import numpy as np
import polars as pl
import joblib
from src.config import Config
from tqdm import tqdm


class ClassifiersApi:
	
	def __init__(self):
		self.classes = ['noisy', 'abstract', 'paint']
		self.models = dict(noisy=joblib.load(Config.noisy_model_path), abstract=joblib.load(Config.abstract_model_path), paint=joblib.load(Config.paint_model_path))
	
	def predict_from_embedding(self, embedding: list[float]) -> dict:
		embedding_np = np.array(embedding).reshape(1, -1)
		predictions = {cls: float(self.models[cls].predict(embedding_np)[0]) for cls in self.classes}
		return predictions

