import numpy as np
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics.pairwise import cosine_similarity
import csv
import os
import json
from typing import List, Dict
from src.features import Features


class Logic:
	
	def __init__(self):
		self.features = Features()
		self.models: dict = dict(embeddings=None, colors=None, overall=None)
		self.log_file_path = os.path.join('logs', 'predictions_log.csv')
		os.makedirs('logs', exist_ok=True)
		self._initialize_log_file()

	def _initialize_log_file(self):
		if not os.path.exists(self.log_file_path):
			with open(self.log_file_path, 'w', newline='') as csvfile:
				writer = csv.writer(csvfile)
				writer.writerow(['prediction_session_id', 'weight', 'liked_ids', 'disliked_ids', 'top_predictions', "feedback_liked", "feedback_disliked"])

	def log_prediction_and_feedback(self, session_id: str, weight:Dict[str, float], liked_ids: List[int], disliked_ids: List[int], top_predictions: List[dict], feedback_liked: List[int] = None, feedback_disliked: List[int] = None):
		"""Logs a new prediction entry or updates an existing one with feedback."""
		if feedback_liked is None:
			feedback_liked = []
		if feedback_disliked is None:
			feedback_disliked = []

		rows = []
		found_and_updated = False

		# Read all rows to find and update the relevant one
		if os.path.exists(self.log_file_path):
			with open(self.log_file_path, 'r', newline='') as csvfile:
				reader = csv.reader(csvfile)
				header = next(reader)

				expected_headers = ['prediction_session_id', 'weight', 'liked_ids', 'disliked_ids', 'top_predictions', "feedback_liked", "feedback_disliked"]
				if header != expected_headers:
					print(f"Warning: CSV header mismatch. Expected {expected_headers}, got {header}. Appending new data.")
					rows.append(header) # Keep existing header if mismatched
				else:
					rows.append(header) # Add header back

				for row in reader:
					if row[0] == session_id:
						# Update the existing row with feedback
						row[5] = json.dumps(feedback_liked)
						row[6] = json.dumps(feedback_disliked)
						found_and_updated = True
					rows.append(row)

		# If a new entry, append it
		if not found_and_updated:
			new_row = [
				session_id,
				json.dumps(weight),
				json.dumps(liked_ids),
				json.dumps(disliked_ids),
				json.dumps(top_predictions),
				json.dumps(feedback_liked),
				json.dumps(feedback_disliked)
			]
			rows.append(new_row)

		# Write all rows back to the CSV file
		with open(self.log_file_path, 'w', newline='') as csvfile:
			writer = csv.writer(csvfile)
			writer.writerows(rows)
		print(f"Logged/updated prediction session {session_id} in {self.log_file_path}")

	def mean_or_zeros(self, data, key, default_shape):
		if data is None or key not in data or data[key] is None:
			return np.zeros(default_shape)
		return np.mean(data[key], axis=0) if data[key].size > 0 else np.zeros(default_shape)

	def score_scalar_feature(self, candidates, liked, disliked, name: str):
		if liked is not None and name in liked and len(liked[name]) > 0:
			liked_val = np.mean(liked[name])
		else:
			liked_val = 0.0

		if disliked is not None and name in disliked and len(disliked[name]) > 0:
			disliked_val = np.mean(disliked[name])
		else:
			disliked_val = 0.0

		return (np.abs(candidates[name] - liked_val) - np.abs(candidates[name] - disliked_val)).reshape(-1, 1)

	def predict(self, image_ids: list[int], target: list[int],session_id, embedding_weight:float=0.4, color_weight:float=0.3, abstract_weight:float=0.1, noisy_weight:float=0.1, paint_weight:float=0.1):
		liked_ids = [id for id, label in zip(image_ids, target) if label == 1]
		disliked_ids = [id for id, label in zip(image_ids, target) if label == 0]
		print(f"{len(liked_ids)=}, {len(disliked_ids)=}")

		# Features
		liked = self.features.get_ids_np(image_ids=liked_ids) if liked_ids else None
		disliked = self.features.get_ids_np(image_ids=disliked_ids) if disliked_ids else None
		candidates = self.features.get_not_ids_np(image_ids=image_ids)
		all_ids = self.features.get_all_ids_np()

		mean_liked_emb = self.mean_or_zeros(liked, 'embeddings', candidates['embeddings'].shape)
		mean_dis_emb = self.mean_or_zeros(disliked, 'embeddings', candidates['embeddings'].shape)
		mean_liked_col = self.mean_or_zeros(liked, 'colors', candidates['colors'].shape[1])
		mean_dis_col = self.mean_or_zeros(disliked, 'colors', candidates['colors'].shape[1])

		sim_liked_emb = cosine_similarity(candidates['embeddings'], mean_liked_emb.reshape(1, -1)).flatten()
		sim_dis_emb = cosine_similarity(candidates['embeddings'], mean_dis_emb.reshape(1, -1)).flatten()
		sim_liked_col = cosine_similarity(candidates['colors'], mean_liked_col.reshape(1, -1)).flatten()
		sim_dis_col = cosine_similarity(candidates['colors'], mean_dis_col.reshape(1, -1)).flatten()

		emb_score = sim_liked_emb - sim_dis_emb
		col_score = sim_liked_col - sim_dis_col
		abstract_score = self.score_scalar_feature(candidates, liked, disliked, 'abstract')
		paint_score = self.score_scalar_feature(candidates, liked, disliked, 'paint')
		noisy_score = self.score_scalar_feature(candidates, liked, disliked, 'noisy')

		abstract_score = np.squeeze(abstract_score)
		paint_score = np.squeeze(paint_score)
		noisy_score = np.squeeze(noisy_score)

		# Final score
		overall_score = (embedding_weight * emb_score + color_weight * col_score + abstract_weight * abstract_score + paint_weight * paint_score + noisy_weight * noisy_score)

		sorted_indexes = np.argsort(overall_score)[::-1]

		score_dict = {
			'overall': overall_score,
			'embeddings': emb_score.flatten(),
			'colors': col_score.flatten(),
			'abstract': abstract_score.flatten(),
			'paint': paint_score.flatten(),
			'noisy': noisy_score.flatten()
		}

		# Prepare details for the predicted top 10 images
		predicted_image_details = []
		for idx in sorted_indexes[:10]:
			image_id = candidates['ids'][idx] # Get the actual ID for the predicted image
			noisy_score, abstract_score, paint_score = candidates['classifiers'][idx] # Get classifier scores for this predicted image

			predicted_image_details.append({
				"id": int(image_id),
				"overall": round(float(score_dict['overall'][idx]), 4),
				"embeddings": round(float(score_dict['embeddings'][idx]), 4),
				"colors": round(float(score_dict['colors'][idx]), 4),
				"noisy": round(float(noisy_score), 4),
				"abstract": round(float(abstract_score), 4),
				"paint": round(float(paint_score), 4)
			})

		weight = {
			'embeddings': embedding_weight,
			'colors': color_weight,
			'abstract': abstract_weight,
			'paint': paint_weight,
			'noisy': noisy_weight
		}

		self.log_prediction_and_feedback(
			session_id=session_id,
			weight=weight,
			liked_ids=liked_ids,
			disliked_ids=disliked_ids,
			top_predictions=predicted_image_details,
			feedback_liked=[],
			feedback_disliked=[]
		)

		return self.features.get_pred_likes(image_ids=image_ids, sorted_indexes=sorted_indexes), overall_score[sorted_indexes], score_dict

		# # get score for each user choice
		# # step 1: for each classifier, get features (color, embeddings, noise, abstract, paint)
		# X_train = self.features.get_ids_np(image_ids=image_ids)
		# y_train = np.array(target)
		# y_train_scores = dict()
		
		# all_ids = self.features.get_all_ids_np()
		# X_pred = self.features.get_not_ids_np(image_ids=image_ids)
		# y_pred_scores = dict()
		# # step 2: train model on user_images - embeddings
		# self.models['embeddings'] = LogisticRegression().fit(X_train['embeddings'], y_train)
		# # print(f"{self.models['embeddings'].predict_proba(X_train['embeddings'])}")
		# y_train_scores['embeddings'] = self.models['embeddings'].predict_proba(X_train['embeddings'])[:, 1].reshape(-1, 1)
		# y_pred_scores['embeddings'] = self.models['embeddings'].predict_proba(X_pred['embeddings'])[:, 1].reshape(-1, 1)
		# # step 3: train model on user_images - colors
		# self.models['colors'] = LogisticRegression().fit(X_train['colors'], y_train)
		# y_train_scores['colors'] = self.models['colors'].predict_proba(X_train['colors'])[:, 1].reshape(-1, 1)
		# y_pred_scores['colors'] = self.models['colors'].predict_proba(X_pred['colors'])[:, 1].reshape(-1, 1)
		
		# # step 4: train model on all the scores from previous steps (noise, abstract, paint, color, embeddings)
		# X_train_scores = np.concatenate([y_train_scores["embeddings"], y_train_scores['colors'], X_train['classifiers']], axis=1)
		# X_pred_scores = np.concatenate([y_pred_scores["embeddings"], y_pred_scores['colors'], X_pred['classifiers']], axis=1)
		# self.models['overall'] = LogisticRegression().fit(X_train_scores, y_train)
		# target_pred = self.models['overall'].predict_proba(X_train_scores)[:, 1]
		# results = self.models['overall'].predict_proba(X_pred_scores)[:, 1]
		# # print(f"{y_pred_scores=}")
		# # print(f"{X_pred_scores=}")
		# # print(f"{results=}")
		# sorted_indexes = np.argsort(results)[::-1]
		# score_dict = {
		# 	'overall': results,
		# 	'embeddings': y_pred_scores['embeddings'].flatten(),
		# 	'colors': y_pred_scores['colors'].flatten(),
		# }

		# if save_predict:
		# 	self.save_prediction_row_to_csv(liked_ids=liked_ids, disliked_ids=disliked_ids, all_image_ids = all_ids, sorted_indexes=sorted_indexes, scores_dict=score_dict, classifiers_array=X_pred['classifiers'])
		# return self.features.get_pred_likes(image_ids=image_ids, sorted_indexes=sorted_indexes), results[sorted_indexes], target_pred
		
		
if __name__ == '__main__':
	l = Logic()
	image_ids = [4217, 1179, 4613, 4405, 2706, 1555, 5055, 1583, 3814, 1742, 4969, 3960]
	target = [0, 1, 0, 0, 1, 0, 1, 1, 2, 0, 1, 1]
	for i in range(2, len(image_ids)):
		print(f'{image_ids[:i]}: {l.predict(image_ids=image_ids[:i], target=target[:i])[0][0]}')


