import os
import sys
import asyncio
import random
import pickle
from tqdm import tqdm
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

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

def save_embeddings(wall_embeddings, art_embeddings, path="embeddings_cache"):
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "wall_embeddings.pkl"), "wb") as f:
        pickle.dump(wall_embeddings, f)
    with open(os.path.join(path, "art_embeddings.pkl"), "wb") as f:
        pickle.dump(art_embeddings, f)

def create_embedding_pairs(pairs, wall_embeddings, art_embeddings):
    """Return dict: {wall,art} → (wall_emb, art_emb)"""
    embeddings_pairs = {}
    for wall_id, art_id in tqdm(pairs, desc="Creating embeddings pairs"):
        key = f"{wall_id},{art_id}"
        print(f"Art ID: {art_id}, Wall ID: {wall_id}, Key: {key}")
        embeddings_pairs[key] = (wall_embeddings[wall_id], art_embeddings[art_id])
    return embeddings_pairs

def create_embedding_pairs_from_files(wall_path, art_path):
    rows = asyncio.run(fetch_wall_selections())
    wall_to_positive = extract_positive_data(rows)

    # Update embeddings only if new IDs appear
    wall_embeddings, art_embeddings = asyncio.run(
        update_embeddings_if_needed(wall_path, art_path, wall_to_positive)
    )

    return create_pairs_from_embeddings(wall_embeddings, art_embeddings, wall_to_positive)

def create_pairs_from_embeddings(wall_embeddings, art_embeddings, wall_to_positive):
    emb_pairs, labels = {}, {}

    for wall_id, selected in wall_to_positive.items():
        all_positive_ids = set().union(*wall_to_positive.values())

        for art_id in selected:
            if wall_id in wall_embeddings and art_id in art_embeddings:
                key = f"{wall_id},{art_id}"
                emb_pairs[key] = (wall_embeddings[wall_id], art_embeddings[art_id])
                labels[key] = 1

        neg_candidates = list(all_positive_ids - set(selected))
        sampled_neg = random.sample(neg_candidates, min(len(neg_candidates), len(selected) * 3))

        for art_id in sampled_neg:
            if wall_id in wall_embeddings and art_id in art_embeddings:
                key = f"{wall_id},{art_id}"
                emb_pairs[key] = (wall_embeddings[wall_id], art_embeddings[art_id])
                labels[key] = 0

    return emb_pairs, labels

async def update_embeddings_if_needed(wall_path, art_path, wall_to_positive):
    """Ensure embeddings cache contains all required walls/artworks."""

    # Load existing if available
    wall_embeddings = {}
    art_embeddings = {}
    if os.path.exists(wall_path):
        with open(wall_path, "rb") as f:
            wall_embeddings = pickle.load(f)
    if os.path.exists(art_path):
        with open(art_path, "rb") as f:
            art_embeddings = pickle.load(f)

    # Required IDs from DB
    required_walls = set(wall_to_positive.keys())
    required_arts = set().union(*wall_to_positive.values())

    # Missing IDs
    missing_walls = required_walls - wall_embeddings.keys()
    missing_arts = required_arts - art_embeddings.keys()

    if missing_walls or missing_arts:
        print(f"⚡ Found {len(missing_walls)} missing walls, {len(missing_arts)} missing artworks. Embedding now...")
        clip = ClipEmbed()

        # Embed missing walls
        for wall_id in tqdm(missing_walls, desc="Embedding new walls"):
            while True:
                try:
                    path = f"{Config.walls_url}{wall_id + 1}.jpg"
                    wall_embeddings[wall_id] = clip.predict_imgs([path])[0]
                    break
                except Exception as e:
                    print(f"Failed to embed wall {wall_id}: {e}, retrying in 0.5s...")
                    await asyncio.sleep(0.5)

        # Embed missing artworks
        for art_id in tqdm(missing_arts, desc="Embedding new artworks"):
            path = f"{Config.images_url}{art_id}.jpg"
            art_embeddings[art_id] = clip.predict_imgs([path])[0]

        # Save updated cache
        save_embeddings(wall_embeddings, art_embeddings, path=os.path.dirname(wall_path))
    else:
        print("✅ No new embeddings needed. Using cached files.")

    return wall_embeddings, art_embeddings