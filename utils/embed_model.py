import clip
import torch
from PIL import Image
import numpy as np
from sklearn.preprocessing import normalize
import requests
from io import BytesIO

def load_image(path_or_url):
    if path_or_url.startswith('http://') or path_or_url.startswith('https://'):
        response = requests.get(path_or_url)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGB")
    else:
        return Image.open(path_or_url).convert("RGB")

class ConfigClip:
	def __init__(self):
		self.available_models = ['RN50', 'RN101', 'RN50x4', 'RN50x16', 'RN50x64', 'ViT-B/32', 'ViT-B/16', 'ViT-L/14', 'ViT-L/14@336px']  # clip.available_models()
		self.device = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'
		self.name = self.available_models[-1]
		self.model_dir = 'volumes'


class ClipEmbed:
	"""
	get embedding for images. the process include: make every image square, the insert into clip, then extract embeddings.
	"""
	
	def __init__(self):
		super().__init__()
		config = ConfigClip()
		
		self.device = config.device
		self.name = config.name
		self.model_dir = config.model_dir
		self.dim = 768
		self.model, self.model_preprocess = clip.load(self.name, device=config.device)
		self.model.eval()
	
	def predict_imgs(self, urls: list[str]) -> np.ndarray:
		# imgs = self.preprocessing(urls)
		
		imgs = [self.model_preprocess(load_image(img_path)) for img_path in urls]
		imgs = torch.stack(imgs).to(self.device)
		
		with torch.no_grad():
			embedding = self.model.encode_image(imgs)
			embedding = embedding.cpu().numpy()
		normalize_embedding = normalize(embedding, norm="l2").astype(np.float32)
		return normalize_embedding
	
	def predict_text(self, texts: list[str]) -> np.ndarray:
		text_tokens = clip.tokenize(texts).to(self.device)
		with torch.no_grad():
			embedding = self.model.encode_text(text_tokens)
			embedding = embedding.cpu().numpy()
		normalize_embedding = normalize(embedding, norm="l2").astype(np.float32)
		return normalize_embedding


def get_embeddings(images: list[str], batch_size=8):
	model = ClipEmbed(ConfigClip())
	embeddings = np.empty((0, 768), dtype=float)
	for i in range(0, len(images), batch_size):
		embeddings = np.concatenate([embeddings, model.predict_imgs(images[i: min(i + batch_size, len(images))])])
	return embeddings
