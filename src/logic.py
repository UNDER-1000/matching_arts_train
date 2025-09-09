import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import SpectralClustering
from collections import defaultdict
import  heapq
from typing import List
import torch

from train.train_walls_art import load_model
from utils.embed_model import ClipEmbed
from src.features import Features
from src.config import Config
from models import Artwork


class Logic:
    def __init__(self, model_path=Config.walls_model_path):
        self.features = Features()
        self.model = load_model(input_dim=1536, path=model_path)
        self.model.eval()
        self.clip = ClipEmbed()

    async def add_artwork(self, artwork: Artwork):
        return await self.features.add_artwork(artwork)

    def mean_or_zeros(self, data, key, default_shape):
        if data is None or key not in data or data[key] is None:
            return np.zeros(default_shape)
        return np.mean(data[key].astype(float), axis=0) if data[key].size > 0 else np.zeros(default_shape)

    def score_scalar_feature(self, candidates, liked, disliked, name: str):
        candidates_col = candidates[name].astype(float)

        has_liked = liked is not None and name in liked and len(liked[name]) > 0
        has_disliked = disliked is not None and name in disliked and len(disliked[name]) > 0

        if has_liked:
            liked_val = np.mean(liked[name].astype(float))
        if has_disliked:
            disliked_val = np.mean(disliked[name].astype(float))

        if has_liked and has_disliked:
            score = np.abs(candidates_col - disliked_val) - np.abs(candidates_col - liked_val)
        elif has_liked:
            score = -np.abs(candidates_col - liked_val)  # closer to liked is better
        elif has_disliked:
            score = np.abs(candidates_col - disliked_val)  # farther from disliked is better
        else:
            score = np.zeros_like(candidates_col)  # no signal

		# Normalize to [-1, 1]
        score_min = score.min()
        score_max = score.max()
        if score_max != score_min:
            normalized_score = 2 * (score - score_min) / (score_max - score_min) - 1
        else:
            normalized_score = np.zeros_like(score)

        return normalized_score.reshape(-1, 1)

    async def predict_artworks(self, artwork_id: List[int], target: List[int], embedding_weight: float = 0.4, color_weight: float = 0.3, abstract_weight: float = 0.1, noisy_weight: float = 0.1, paint_weight: float = 0.1):
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

        top_30_indexes = sorted_indexes[:30]
        top_30_embeddings = candidates['embeddings'][top_30_indexes]

        n_clusters = min(5, len(top_30_embeddings))
        clustering = SpectralClustering(n_clusters=n_clusters, affinity='nearest_neighbors', assign_labels='kmeans', random_state=42)
        labels = clustering.fit_predict(top_30_embeddings)

        clusters = defaultdict(list)
        for idx, label in zip(top_30_indexes, labels):
            clusters[label].append(idx)

        selected_indexes = []
        for cluster in clusters.values():
            top_in_cluster = heapq.nlargest(2, cluster, key=lambda idx: overall_score[idx])
            selected_indexes.extend(top_in_cluster)

        if len(selected_indexes) < 10:
            extras = [idx for idx in sorted_indexes if idx not in selected_indexes]
            selected_indexes += extras[:10 - len(selected_indexes)]

        selected_indexes = sorted(selected_indexes, key=lambda idx: overall_score[idx], reverse=True)

        # Prepare details for the predicted top 10 images
        top_predictions = []
        for idx in selected_indexes:
            top_predictions.append(candidates['ids'][idx])

        return top_predictions
    
    async def predict_walls(self, wall_path, k=30):
        print("Predicting walls...")
        wall_embedding = self.clip.predict_imgs([wall_path])[0]
        wall_tensor = torch.tensor(wall_embedding, dtype=torch.float32).unsqueeze(0)

        scores = {}
        candidates = await self.features.get_all_ids_with_embeddings_np()
        with torch.no_grad():
            for art_id, feature in zip(candidates["ids"], candidates["embeddings"]):
                art_embedding = feature
                art_tensor = torch.tensor(art_embedding, dtype=torch.float32).unsqueeze(0)
                input_tensor = torch.cat((wall_tensor, art_tensor), dim=1)
                score = self.model(input_tensor).item()
                scores[art_id] = score

        # Get top-k recommendations
        top_k = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
        top_k_ids, top_k_scores = zip(*top_k)
        top_k_str = [str(id) for id in top_k_ids]
        return top_k_str

if __name__ == '__main__':
	l = Logic()
	artwork_id = [4217, 1179, 4613, 4405, 2706, 1555, 5055, 1583, 3814, 1742, 4969, 3960]
	target = [0, 1, 0, 0, 1, 0, 1, 1, 2, 0, 1, 1]
	for i in range(2, len(artwork_id)):
		print(f'{artwork_id[:i]}: {l.predict(artwork_id=artwork_id[:i], target=target[:i])[0][0]}')


