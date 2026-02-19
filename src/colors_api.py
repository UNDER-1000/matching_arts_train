import numpy as np
import cv2
import polars as pl
import json
from PIL import Image
from src.config import Config
import requests
from io import BytesIO
from tqdm import tqdm

class ColorsApi:
	
	def __init__(self):
		self.n_bins = Config.colors_n_bins
	
	def predict_from_path(self, image_path: str) -> list[float]:
		if image_path.startswith("http://") or image_path.startswith("https://"):
			response = requests.get(image_path)
			response.raise_for_status()
			pil_image = Image.open(BytesIO(response.content))
		else:
			pil_image = Image.open(image_path)
		
		# Convert grayscale images to RGB
		if pil_image.mode != 'RGB':
			pil_image = pil_image.convert('RGB')
		
		cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2HSV)
		
		h = (cv_image[:, :, 0] / 180 * self.n_bins).astype(int)
		h = np.clip(h, 0, self.n_bins - 1)
		
		unique_values, counts = np.unique(h, return_counts=True)
		color_histogram = np.zeros(self.n_bins)
		color_histogram[unique_values] = counts
		colors_vec = color_histogram / np.linalg.norm(color_histogram)
		
		return colors_vec.tolist()

