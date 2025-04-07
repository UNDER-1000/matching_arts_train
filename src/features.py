from src.classifiers_api import ClassifiersApi
from src.colors_api import ColorsApi
from src.embeddings_api import EmbeddingsApi
import numpy as np
import json
import polars as pl
from src.config import Config
import os


class Features:
	
	def __init__(self):
		self.csv_name = Config.csv_name
		self.image_ids = self.read_images_ids()
		self.embeddings_api = EmbeddingsApi()
		self.classifier_api = ClassifiersApi()
		self.colors_api = ColorsApi()
		
		if Config.restart:
			colors_df = self.colors_api.pp(image_ids=self.image_ids)
			embeddings_df = self.embeddings_api.pp(image_ids=self.image_ids)
			embeddings = np.array([json.loads(e) for e in embeddings_df['embeddings']])
			classifier_df = self.classifier_api.pp(embeddings=embeddings, image_ids=self.image_ids)
			self.combined_df = pl.concat([embeddings_df, colors_df.drop("image_ids"), classifier_df.drop("image_ids")], how="horizontal")
			self.combined_df.write_csv(self.csv_name)
		
		else:
			self.combined_df = pl.read_csv(self.csv_name)
		
		print(len(self.combined_df))
	
	def get_ids_np(self, image_ids):
		selected_rows = self.combined_df.filter(pl.col("image_ids").is_in(image_ids))
		embeddings = np.array([json.loads(e) for e in selected_rows['embeddings']])
		colors = np.array([json.loads(e) for e in selected_rows['colors']])
		classifiers = np.array(selected_rows.select([col for col in selected_rows.columns if col in self.classifier_api.classes]))
		return dict(embeddings=embeddings, colors=colors, classifiers=classifiers)

	def get_not_ids_np(self, image_ids):
		selected_rows = self.combined_df.filter(~pl.col("image_ids").is_in(image_ids))
		embeddings = np.array([json.loads(e) for e in selected_rows['embeddings']])
		colors = np.array([json.loads(e) for e in selected_rows['colors']])
		classifiers = np.array(selected_rows.select([col for col in selected_rows.columns if col in self.classifier_api.classes]))
		return dict(embeddings=embeddings, colors=colors, classifiers=classifiers)
	
	def get_pred_likes(self, image_ids, sorted_indexes):
		selected_rows = self.combined_df.filter(~pl.col("image_ids").is_in(image_ids))
		image_id_list = selected_rows["image_ids"].to_list()
		sorted_image_ids = [image_id_list[i] for i in sorted_indexes]
		return sorted_image_ids
	
	def read_images_ids(self):
		self.image_ids = []
		for img in os.listdir(Config.images_folder):
			if not img.endswith('.jpg'):
				continue
			self.image_ids.append(img[:-4])
		return self.image_ids
	

if __name__ == '__main__':
	f = Features()
