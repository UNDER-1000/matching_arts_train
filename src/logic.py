import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import csv
import os
import json
from typing import List, Dict
from src.features import Features
from models import Artwork


class Logic:
    def __init__(self):
        self.features = Features()

    async def add_artwork(self, artwork: Artwork):
        return await self.features.add_artwork(artwork)

    def mean_or_zeros(self, data, key, default_shape):
        if data is None or key not in data or data[key] is None:
            return np.zeros(default_shape)
        return np.mean(data[key].astype(float), axis=0) if data[key].size > 0 else np.zeros(default_shape)

    def score_scalar_feature(self, candidates, liked, disliked, name: str):
        liked_val = np.mean(liked[name].astype(float)) if liked and name in liked and len(liked[name]) > 0 else 0.0
        disliked_val = np.mean(disliked[name].astype(float)) if disliked and name in disliked and len(disliked[name]) > 0 else 0.0
        return (np.abs(candidates[name].astype(float) - liked_val) - np.abs(candidates[name].astype(float) - disliked_val)).reshape(-1, 1)

    async def predict(self, artwork_id: List[int], target: List[int], embedding_weight: float = 0.4, color_weight: float = 0.3, abstract_weight: float = 0.1, noisy_weight: float = 0.1, paint_weight: float = 0.1):
        liked_ids = [id for id, label in zip(artwork_id, target) if label == 1]
        disliked_ids = [id for id, label in zip(artwork_id, target) if label == 0]
        print(f"{len(liked_ids)=}, {len(disliked_ids)=}")

        liked = await self.features.get_ids_np(artwork_id=liked_ids) if liked_ids else None
        disliked = await self.features.get_ids_np(artwork_id=disliked_ids) if disliked_ids else None
        candidates = await self.features.get_not_ids_np(artwork_id=artwork_id)

        mean_liked_emb = self.mean_or_zeros(liked, 'embeddings', candidates['embeddings'].shape[1])
        mean_dis_emb = self.mean_or_zeros(disliked, 'embeddings', candidates['embeddings'].shape[1])
        mean_liked_col = self.mean_or_zeros(liked, 'colors', candidates['colors'].shape[1])
        mean_dis_col = self.mean_or_zeros(disliked, 'colors', candidates['colors'].shape[1])

        sim_liked_emb = cosine_similarity(candidates['embeddings'], mean_liked_emb.reshape(1, -1)).flatten()
        sim_dis_emb = cosine_similarity(candidates['embeddings'], mean_dis_emb.reshape(1, -1)).flatten()
        sim_liked_col = cosine_similarity(candidates['colors'], mean_liked_col.reshape(1, -1)).flatten()
        sim_dis_col = cosine_similarity(candidates['colors'], mean_dis_col.reshape(1, -1)).flatten()

        emb_score = sim_liked_emb - sim_dis_emb
        col_score = sim_liked_col - sim_dis_col
        abstract_score = np.squeeze(self.score_scalar_feature(candidates, liked, disliked, 'abstract'))
        paint_score = np.squeeze(self.score_scalar_feature(candidates, liked, disliked, 'paint'))
        noisy_score = np.squeeze(self.score_scalar_feature(candidates, liked, disliked, 'noisy'))

        overall_score = (embedding_weight * emb_score + color_weight * col_score + abstract_weight * abstract_score + paint_weight * paint_score + noisy_weight * noisy_score)
        sorted_indexes = np.argsort(overall_score)[::-1]

        score_dict = {
            'overall': overall_score,
            'embeddings': emb_score,
            'colors': col_score,
            'abstract': abstract_score,
            'paint': paint_score,
            'noisy': noisy_score
        }

        return await self.features.get_pred_likes(artwork_id=artwork_id, sorted_indexes=sorted_indexes), overall_score[sorted_indexes], score_dict


if __name__ == '__main__':
	l = Logic()
	artwork_id = [4217, 1179, 4613, 4405, 2706, 1555, 5055, 1583, 3814, 1742, 4969, 3960]
	target = [0, 1, 0, 0, 1, 0, 1, 1, 2, 0, 1, 1]
	for i in range(2, len(artwork_id)):
		print(f'{artwork_id[:i]}: {l.predict(artwork_id=artwork_id[:i], target=target[:i])[0][0]}')


