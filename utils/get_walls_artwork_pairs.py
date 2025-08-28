from PIL import Image
import math
import os
import sys
import asyncio
import random
import pickle
from tqdm import tqdm
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from io import BytesIO
import aiohttp
import albumentations as A
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.config import Config
from utils.embed_model import ClipEmbed
# from src.colors_api import ColorsApi


async def fetch_wall_selections():
    db_url = Config.db_walls_url
    table_name = "wall_selections"
    engine = create_async_engine(db_url, echo=False)

    while True:
        try:
            async with engine.begin() as conn:
                result = await conn.execute(
                    text(f"SELECT wall_index, selected_artworks FROM {table_name}")
                )
                return result.fetchall()
        except Exception as e:
            print(f"DB query failed: {e}, retrying in 10s...")
            await asyncio.sleep(10)

def extract_positive_data(rows):
    wall_to_positive = {}

    for wall, artworks in rows:
        pos_ids = [int(art.strip()) for art in artworks]
        wall_to_positive[wall] = pos_ids

    return wall_to_positive

def create_balanced_pairs(wall_to_positive, neg_ratio=1.0):
    pairs, labels = [], {}
    for wall, pos_ids in wall_to_positive.items():
        pos_set = set(pos_ids)
        all_positive_ids = set().union(*wall_to_positive.values())
        neg_pool = list(all_positive_ids - pos_set)
        num_neg = min(int(len(pos_ids) * neg_ratio), len(neg_pool))

        for pid in pos_ids:
            pairs.append((wall, pid))
            labels[f"{wall},{pid}"] = 1

        for nid in random.sample(neg_pool, num_neg):
            pairs.append((wall, nid))
            labels[f"{wall},{nid}"] = 0

    return pairs, labels

async def load_wall_artwork_pairs(neg_ratio=1.0):
    rows = await fetch_wall_selections()
    wall_to_positive = extract_positive_data(rows)
    pairs, labels = create_balanced_pairs(wall_to_positive, neg_ratio)
    return pairs, labels

async def create_all_embeddings(wall_ids, artwork_ids):
    """Create and cache all wall and artwork embeddings."""
    clip = ClipEmbed()

    augmanted_embeddings = await create_augmented_embeddings(clip, artwork_ids)
    wall_embeddings = {}
    print("Embedding wall images...")
    for wall_id in tqdm(wall_ids):
        while True:
            try:
                path = f"{Config.walls_url}{wall_id + 1}.jpg"
                wall_embeddings[wall_id] = clip.predict_imgs([path])[0]
                break
            except Exception as e:
                print(f"Failed to embed wall {wall_id}: {e}, retrying in 0.5s...")
                await asyncio.sleep(0.5)

    art_embeddings = {}
    print("Embedding artwork images...")
    for art_id in tqdm(artwork_ids):
        path = f"{Config.images_url}{art_id}.jpg"
        art_embeddings[art_id] = clip.predict_imgs([path])[0]


    return wall_embeddings, art_embeddings, augmanted_embeddings


def save_embeddings(wall_embeddings, art_embeddings, augmented_embeddings, path="embeddings_cache"):
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "wall_embeddings.pkl"), "wb") as f:
        pickle.dump(wall_embeddings, f)
    with open(os.path.join(path, "art_embeddings.pkl"), "wb") as f:
        pickle.dump(art_embeddings, f)
    with open(os.path.join(path, "augmented_embeddings.pkl"), "wb") as f:
        pickle.dump(augmented_embeddings, f)

def load_embeddings(wall_path, art_path, augmented_path):
    with open(wall_path, "rb") as f:
        wall_embeddings = pickle.load(f)
    with open(art_path, "rb") as f:
        art_embeddings = pickle.load(f)
    with open(augmented_path, "rb") as f:
        augmented_embeddings = pickle.load(f)
    return wall_embeddings, art_embeddings, augmented_embeddings

def create_embedding_pairs(pairs, wall_embeddings, art_embeddings):
    """Return dict: {wall,art} → (wall_emb, art_emb)"""
    embeddings_pairs = {}
    for wall_id, art_id in tqdm(pairs, desc="Creating embeddings pairs"):
        key = f"{wall_id},{art_id}"
        print(f"Art ID: {art_id}, Wall ID: {wall_id}, Key: {key}")
        embeddings_pairs[key] = (wall_embeddings[wall_id], art_embeddings[art_id])
    return embeddings_pairs

def create_embedding_pairs_from_files(wall_path, art_path, augmented_path):
    if not os.path.exists(wall_path) or not os.path.exists(art_path) or not os.path.exists(augmented_path):
        pairs, labels = asyncio.run(load_wall_artwork_pairs(neg_ratio=4.0))

        wall_ids = list({wall for wall, _ in pairs})
        art_ids = list({art for _, art in pairs})

        wall_embeddings, art_embeddings, augmented_embeddings = asyncio.run(create_all_embeddings(wall_ids, art_ids))
        save_embeddings(wall_embeddings, art_embeddings, augmented_embeddings, path="embeddings_cache")

    wall_embeddings, art_embeddings, augmented_embeddings = load_embeddings(wall_path, art_path, augmented_path)
    rows = asyncio.run(fetch_wall_selections())
    wall_to_positive = extract_positive_data(rows)
    return create_pairs_from_embeddings(wall_embeddings, art_embeddings, augmented_embeddings, wall_to_positive)

def create_pairs_from_embeddings(wall_embeddings, art_embeddings, augmented_embeddings, wall_to_positive):
    emb_pairs, labels = {}, {}

    for wall_id, selected in wall_to_positive.items():
        all_positive_ids = set().union(*wall_to_positive.values())

        for art_id in selected:
            if wall_id in wall_embeddings and art_id in art_embeddings:
                key = f"{wall_id},{art_id}"
                emb_pairs[key] = (wall_embeddings[wall_id], art_embeddings[art_id])
                labels[key] = 1

                # Add augmented positives (if exist)
                if art_id in augmented_embeddings:
                    for i, aug_emb in enumerate(augmented_embeddings[art_id]):
                        key = f"{wall_id},{art_id}_aug{i}"
                        emb_pairs[key] = (wall_embeddings[wall_id], aug_emb)
                        labels[key] = 1
                        labels[f"{wall_id},{art_id}_aug{i}"] = 1

        neg_candidates = list(all_positive_ids - set(selected))
        sampled_neg = random.sample(neg_candidates, min(len(neg_candidates), len(selected) * 3))

        for art_id in sampled_neg:
            if wall_id in wall_embeddings and art_id in art_embeddings:
                key = f"{wall_id},{art_id}"
                emb_pairs[key] = (wall_embeddings[wall_id], art_embeddings[art_id])
                labels[key] = 0

    return emb_pairs, labels


async def fetch_image(session, url):
    """Fetch image from a URL and return a PIL Image."""
    async with session.get(url) as resp:
        if resp.status != 200:
            raise Exception(f"HTTP {resp.status} for {url}")
        data = await resp.read()
        return Image.open(BytesIO(data)).convert("RGB")
    
def get_augment_pipelines():
    return [
        # Color & lighting
        A.Compose([
            A.RandomBrightnessContrast(0.3, 0.3, p=1),
            A.HueSaturationValue(20, 25, 20, p=1),
        ]),
        # Blur & noise
        A.Compose([
            A.MotionBlur(blur_limit=5, p=1),
            A.GaussNoise(var_limit=(10, 50), p=1),
        ]),
        # Geometry
        A.Compose([
            A.HorizontalFlip(p=0.5),
            A.Rotate(limit=25, p=0.7),
            A.RandomResizedCrop(size=(224, 224), scale=(0.7, 1.0), p=1),
        ]),
        # Compression & artifacts
        A.Compose([
            A.ImageCompression(quality_lower=50, quality_upper=90, p=1),
            A.Downscale(scale_min=0.5, scale_max=0.9, p=0.5),  # simulate low-res
        ])
    ]

async def create_augmented_embeddings(clip, urls):
    """Create augmented embeddings for a list of image URLs."""
    augmentations = get_augment_pipelines()
    all_embeddings = {}

    async with aiohttp.ClientSession() as session:
        for url in tqdm(urls, desc="Creating augmented embeddings"):
            try:
                image = await fetch_image(session, f"{Config.images_url}{url}.jpg")
            except Exception as e:
                print(f"Failed to fetch {url}: {e}")
                continue

            augmented_images = [aug(image=np.array(image))["image"] for aug in augmentations]
            temp_urls = [f"temp_aug_{i}.jpg" for i in range(len(augmented_images))]

            for i, aug_image in enumerate(augmented_images):
                Image.fromarray(aug_image).save(temp_urls[i])
            embeddings = clip.predict_imgs(temp_urls)
            all_embeddings[url] = embeddings

            for temp_url in temp_urls:
                os.remove(temp_url)

    return all_embeddings

if __name__ == "__main__":
    # Load data and generate positive/negative pairs
    pairs, labels = asyncio.run(load_wall_artwork_pairs())

    wall_ids = list({wall for wall, _ in pairs})
    art_ids = list({art for _, art in pairs})

    # Embed each wall/artwork once
    wall_embeddings, art_embeddings, _ = asyncio.run(create_all_embeddings(wall_ids, art_ids))

    # (Optional) Save for reuse
    save_embeddings(wall_embeddings, art_embeddings)

    # Create (wall, artwork) → embedding pairs
    embeddings_pairs = create_embedding_pairs(pairs, wall_embeddings, art_embeddings)

    print(f"✅ Total pairs: {len(embeddings_pairs)}")
    print(f"✅ Positives: {sum(1 for v in labels.values() if v == 1)}")
    print(f"✅ Negatives: {sum(1 for v in labels.values() if v == 0)}")