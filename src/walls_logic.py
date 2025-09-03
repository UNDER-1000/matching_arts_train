import torch
import numpy as np

from src.config import Config
from train.train_walls_art import load_model
from utils.get_walls_artwork_pairs import load_embeddings
from utils.embed_model import ClipEmbed

class PredictionWalls:
    def __init__(self, model_path=Config.walls_model_path):
        self.model = load_model(input_dim=1536, path=model_path)
        self.model.eval()
        self.clip = ClipEmbed()
        wall_embeddings, art_embeddings = load_embeddings(
            wall_path="embeddings_cache/wall_embeddings.pkl",
            art_path="embeddings_cache/art_embeddings.pkl"
        )
        self.image_embeddings = art_embeddings
        self.wall_embeddings = wall_embeddings

    def predict(self, wall_path, k=30):
        wall_embedding = self.clip.predict_imgs([wall_path])[0]
        wall_tensor = torch.tensor(wall_embedding, dtype=torch.float32).unsqueeze(0)

        scores = {}
        with torch.no_grad():
            for art_id, feature in self.image_embeddings.items():
                art_embedding = feature
                art_tensor = torch.tensor(art_embedding, dtype=torch.float32).unsqueeze(0)
                input_tensor = torch.cat((wall_tensor, art_tensor), dim=1)
                score = self.model(input_tensor).item()
                scores[art_id] = score

        # Get top-k recommendations
        all_items_sort = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        print(f"All items sorted: {all_items_sort}")
        top_k = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
        top_k_ids, top_k_scores = zip(*top_k)
        top_k_str = [str(id) for id in top_k_ids]
        return top_k_str, top_k_scores, top_k_ids