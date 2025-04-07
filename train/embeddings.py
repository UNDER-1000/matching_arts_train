import clip
import torch
from PIL import Image, ImageOps
import numpy as np
from sklearn.preprocessing import normalize


class EmbedModel:
	
	def __init__(self):
		pass
	
	def preprocessing(self, imgs: list[str]):
		"""
		make each image square of 224 with padding for a batch of images
		"""
		processed_images = []
		for img_path in imgs:
			img = Image.open(img_path).convert("RGB")
			img.thumbnail((224, 224), Image.Resampling.BICUBIC)
			img = img.resize((224, 224), Image.Resampling.BICUBIC)
			padding = ((224 - img.width) // 2, (224 - img.height) // 2, (224 - img.width) // 2, (224 - img.height) // 2,)
			img = ImageOps.expand(img, padding, (255, 255, 255))
			assert img.size[-1] == 224 and img.size[-2] == 224, f'expecting shape of [3, 224, 224] got: {img.size}'
			processed_images.append(img)
		# processed_images[0].show()
		batch_tensor = torch.stack([torch.from_numpy(np.array(image)).float().permute(2, 0, 1) / 255.0 for image in processed_images])
		return batch_tensor
	
	def predict_imgs(self, urls: list[str]) -> np.ndarray:
		pass
	
	def predict_text(self, texts: list[str]) -> np.ndarray:
		pass


class ConfigClip:
	def __init__(self):
		self.available_models = ['RN50', 'RN101', 'RN50x4', 'RN50x16', 'RN50x64', 'ViT-B/32', 'ViT-B/16', 'ViT-L/14', 'ViT-L/14@336px']  # clip.available_models()
		self.device = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'
		self.name = self.available_models[-1]
		self.model_dir = 'volumes'


class ClipEmbed(EmbedModel):
	"""
	get embedding for images. the process include: make every image square, the insert into clip, then extract embeddings.
	"""
	
	def __init__(self, config: ConfigClip):
		super().__init__()
		
		self.device = config.device
		self.name = config.name
		self.model_dir = config.model_dir
		self.dim = 768
		self.model, self.model_preprocess = clip.load(self.name, device=config.device)
		self.model.eval()
	
	def predict_imgs(self, urls: list[str]) -> np.ndarray:
		# imgs = self.preprocessing(urls)
		
		imgs = [self.model_preprocess(Image.open(img_path).convert("RGB")) for img_path in urls]
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
	