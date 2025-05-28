from src.classifiers_api import ClassifiersApi
from src.colors_api import ColorsApi
from src.embeddings_api import EmbeddingsApi
import numpy as np
import json
import polars as pl
from src.config import Config
from models import Artwork
import os


class Features:
	
	def __init__(self, real_api=False):
		self.embeddings_api = EmbeddingsApi()
		self.classifier_api = ClassifiersApi()
		self.colors_api = ColorsApi()
		if real_api:
			self.combined_df = pl.read_csv(Config.real_csv)
			self.csv_name = Config.real_csv
		else:
			self.csv_name = Config.csv_name
			self.artwork_id = self.read_images_ids()
			
			if Config.restart:
				colors_df = self.colors_api.pp(artwork_id=self.artwork_id)
				embeddings_df = self.embeddings_api.pp(artwork_id=self.artwork_id)
				embeddings = np.array([json.loads(e) for e in embeddings_df['embeddings']])
				classifier_df = self.classifier_api.pp(embeddings=embeddings, artwork_id=self.artwork_id)
				self.combined_df = pl.concat([embeddings_df, colors_df.drop("artwork_id"), classifier_df.drop("artwork_id")], how="horizontal")
				self.combined_df.write_csv(self.csv_name)
			
			else:
				self.combined_df = pl.read_csv(self.csv_name)
		
			print(f"{len(self.combined_df)=}")
	
	def get_ids_np(self, artwork_id):
		selected_rows = self.combined_df.filter(pl.col("artwork_id").is_in(artwork_id))
		embeddings = np.array([json.loads(e) for e in selected_rows['embeddings']])
		colors = np.array([json.loads(e) for e in selected_rows['colors']])
		classifiers = np.array(selected_rows.select([col for col in selected_rows.columns if col in self.classifier_api.classes]))
		return dict(embeddings=embeddings, colors=colors, classifiers=classifiers, abstract=np.array(selected_rows['abstract']), noisy=np.array(selected_rows['noisy']), paint=np.array(selected_rows['paint']))

	def get_not_ids_np(self, artwork_id):
		selected_rows = self.combined_df.filter(~pl.col("artwork_id").is_in(artwork_id))
		embeddings = np.array([json.loads(e) for e in selected_rows['embeddings']])
		colors = np.array([json.loads(e) for e in selected_rows['colors']])
		classifiers = np.array(selected_rows.select([col for col in selected_rows.columns if col in self.classifier_api.classes]))
		ids = np.array(selected_rows['artwork_id'])
		return dict(embeddings=embeddings, colors=colors, classifiers=classifiers, abstract=np.array(selected_rows['abstract']), noisy=np.array(selected_rows['noisy']), paint=np.array(selected_rows['paint']), ids=ids)

	def get_all_ids_np(self):
		return np.array(self.combined_df['artwork_id'])
	
	def get_pred_likes(self, artwork_id, sorted_indexes):
		selected_rows = self.combined_df.filter(~pl.col("artwork_id").is_in(artwork_id))
		image_id_list = selected_rows["artwork_id"].to_list()
		sorted_artwork_id = [image_id_list[i] for i in sorted_indexes]
		return sorted_artwork_id
	
	def read_images_ids(self):
		self.artwork_id = []
		for img in os.listdir(Config.images_folder):
			if not img.endswith('.jpg'):
				continue
			self.artwork_id.append(img[:-4])
		return self.artwork_id

	def add_artwork(self, artwork: Artwork):
		"""Add an artwork and its features to the combined DataFrame and update CSV."""
		if artwork.artwork_id in self.combined_df['artwork_id'].to_list():
			print(f"Artwork {artwork.artwork_id} already exists.")
			return False

		# Get features
		colors = [self.colors_api.predict_from_path(path) for path in artwork.images]
		avg_color = np.mean(colors, axis=0)

		embeddings = [self.embeddings_api.predict_from_path(path) for path in artwork.images]
		avg_embedding = np.mean(embeddings, axis=0)

		classifier_preds = self.classifier_api.predict_from_embedding(avg_embedding)

		# Build the new row
		new_row = {
			"artwork_id": artwork.artwork_id,
			"artist_id": artwork.artist_id,
			"artist_name": artwork.artist_name,
			"artwork_name": artwork.artwork_name,
			"images": json.dumps(artwork.images),
			"description": artwork.description or "",
			"category": artwork.category or "",
			"properties": json.dumps({
				"media": artwork.media,
				"medium": artwork.medium,
				"size": artwork.size,
				"price": artwork.price,
				"styles": artwork.styles,
				"subject": artwork.subject,
			}),
			"embeddings": json.dumps(avg_embedding.tolist()),
			"colors": json.dumps(avg_color.tolist()),
			"abstract": float(classifier_preds['abstract']),
			"noisy": float(classifier_preds['noisy']),
			"paint": float(classifier_preds['paint']),
		}

		# Append to DataFrame and save
		new_df = pl.DataFrame([new_row])
		for column in self.combined_df.columns:
			if column in new_df.columns:
				new_df = new_df.with_columns(
					new_df[column].cast(self.combined_df.schema[column])
				)
		self.combined_df = pl.concat([self.combined_df, new_df], how="vertical")
		self.combined_df.write_csv(self.csv_name)
		return True





if __name__ == '__main__':
	f = Features()
