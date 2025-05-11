import numpy as np
from sklearn.linear_model import LogisticRegression, LinearRegression
import numpy as np
from src.features import Features


class Logic:
	
	def __init__(self):
		self.features = Features()
		self.models: dict = dict(embeddings=None, colors=None, overall=None)
	
	def predict(self, image_ids: list[int], target: list[int]):  # target: 0 for disliked, 1 for like

		# get score for each user choice
		# step 1: for each classifier, get features (color, embeddings, noise, abstract, paint)
		X_train = self.features.get_ids_np(image_ids=image_ids)
		y_train = np.array(target)
		y_train_scores = dict()
		
		X_pred = self.features.get_not_ids_np(image_ids=image_ids)
		y_pred_scores = dict()
		# step 2: train model on user_images - embeddings
		self.models['embeddings'] = LogisticRegression().fit(X_train['embeddings'], y_train)
		print(f"{self.models['embeddings'].predict_proba(X_train['embeddings'])}")
		y_train_scores['embeddings'] = self.models['embeddings'].predict_proba(X_train['embeddings'])[:, 1].reshape(-1, 1)
		y_pred_scores['embeddings'] = self.models['embeddings'].predict_proba(X_pred['embeddings'])[:, 1].reshape(-1, 1)
		# step 3: train model on user_images - colors
		self.models['colors'] = LogisticRegression().fit(X_train['colors'], y_train)
		y_train_scores['colors'] = self.models['colors'].predict_proba(X_train['colors'])[:, 1].reshape(-1, 1)
		y_pred_scores['colors'] = self.models['colors'].predict_proba(X_pred['colors'])[:, 1].reshape(-1, 1)
		
		# step 4: train model on all the scores from previous steps (noise, abstract, paint, color, embeddings)
		X_train_scores = np.concatenate([y_train_scores["embeddings"], y_train_scores['colors'], X_train['classifiers']], axis=1)
		X_pred_scores = np.concatenate([y_pred_scores["embeddings"], y_pred_scores['colors'], X_pred['classifiers']], axis=1)
		self.models['overall'] = LogisticRegression().fit(X_train_scores, y_train)
		target_pred = self.models['overall'].predict_proba(X_train_scores)[:, 1]
		results = self.models['overall'].predict_proba(X_pred_scores)[:, 1]
		# print(f"{y_pred_scores=}")
		# print(f"{X_pred_scores=}")
		# print(f"{results=}")
		sorted_indexes = np.argsort(results)[::-1]
		return self.features.get_pred_likes(image_ids=image_ids, sorted_indexes=sorted_indexes), results[sorted_indexes], target_pred
		
		
if __name__ == '__main__':
	l = Logic()
	image_ids = [4217, 1179, 4613, 4405, 2706, 1555, 5055, 1583, 3814, 1742, 4969, 3960]
	target = [0, 1, 0, 0, 1, 0, 1, 1, 2, 0, 1, 1]
	for i in range(2, len(image_ids)):
		print(f'{image_ids[:i]}: {l.predict(image_ids=image_ids[:i], target=target[:i])[0][0]}')


