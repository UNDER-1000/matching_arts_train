import numpy as np
import cv2
import polars as pl
import json
from PIL import Image
from src.config import Config


class ColorsApi:
	
	def __init__(self):
		self.images_folder = Config.images_folder
		self.n_bins = Config.colors_n_bins
	
	def pp(self, image_ids):
		return self.predict_all(image_ids)
	
	def predict_all(self, image_ids: list[str]):
		results = self.predict_batch(image_ids)
		
		df = pl.DataFrame({"image_ids": image_ids, "colors": [json.dumps(color.tolist()) for color in results]})
		return df
		
	def predict_batch(self, image_ids: list[str]):
		pil_images = [Image.open(f"{self.images_folder}{img}.jpg") for img in image_ids]
		cv2_images = []
		for pil_image in pil_images:
			cv2_images.append(cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2HSV))
		
		results = np.empty((len(cv2_images), self.n_bins))
		for i, image in enumerate(cv2_images):
			h = (image[:, :, 0] / 180 * self.n_bins).astype(int)
			h = np.clip(h, 0, self.n_bins - 1)
			
			unique_values, counts = np.unique(h, return_counts=True)
			color_histogram = np.zeros(self.n_bins)
			color_histogram[unique_values] = counts
			colors_vec = color_histogram / np.linalg.norm(color_histogram)
			results[i] = np.array(colors_vec)
		return results
