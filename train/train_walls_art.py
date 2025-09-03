import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader, random_split
from sklearn.model_selection import train_test_split

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.get_walls_artwork_pairs import create_embedding_pairs_from_files

# 2. Prepare training data: concatenate embeddings and collect labels
def prepare_dataset(embeddings_pairs, labels):
    X = []
    y = []
    for key, (wall_emb, art_emb) in embeddings_pairs.items():
        if key in labels:
            combined = np.concatenate([wall_emb, art_emb])  # shape: (2 * embedding_dim,)
            X.append(combined)
            y.append(labels[key])
    return np.array(X), np.array(y)

def split_dataset_by_wall(X, y, pairs, val_ratio=0.25, seed=42):
    """
    Split dataset so that no wall ID appears in both train and validation.
    
    Args:
        X: np.array, features
        y: np.array, labels
        pairs: list of (wall_id, art_id) in the same order as X, y
        val_ratio: fraction of walls to put in validation
    """
    rng = np.random.RandomState(seed)

    # Collect unique wall IDs
    walls = list({wall for wall, _ in pairs})
    rng.shuffle(walls)

    n_val = int(len(walls) * val_ratio)
    val_walls = set(walls[:n_val])
    train_walls = set(walls[n_val:])

    # Split based on wall membership
    train_idx, val_idx = [], []
    for i, (wall, art) in enumerate(pairs):
        if wall in train_walls:
            train_idx.append(i)
        else:
            val_idx.append(i)

    X_train, y_train = X[train_idx], y[train_idx]
    X_val, y_val = X[val_idx], y[val_idx]

    return (X_train, y_train), (X_val, y_val)


def split_dataset(X, y, val_ratio=0.25, seed=42):
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=val_ratio, random_state=seed, stratify=y)
    return (X_train, y_train), (X_val, y_val)

# 3. Define the model (simple MLP)
class WallArtClassifier(nn.Module):
    def __init__(self, input_dim, dropout_rate=0.5):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(64, 16),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.model(x)

# 4. Train the model
def train_model(model, train_loader, val_loader, epochs=10, lr=1e-3, weight_decay=1e-5):
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    train_losses = []
    val_losses = []

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for X_batch, y_batch in train_loader:
            pred = model(X_batch)
            loss = criterion(pred, y_batch)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        avg_loss = total_loss / len(train_loader)

        val_loss = evaluate_model(model, val_loader)
        print(f"Epoch {epoch+1}: Train Loss = {avg_loss:.4f} | Val Loss = {val_loss:.4f}")
        train_losses.append(avg_loss)
        val_losses.append(val_loss)

    return model, train_losses, val_losses

def evaluate_model(model, loader):
    model.eval()
    total_loss = 0
    criterion = nn.BCELoss()
    with torch.no_grad():
        for xb, yb in loader:
            pred = model(xb)
            loss = criterion(pred, yb)
            total_loss += loss.item()
    return total_loss / len(loader)

# 5. Save model
def save_model(model, path="wall_art_model.pt"):
    torch.save(model.state_dict(), path)

# 6. Load model for inference
def load_model(input_dim, path="wall_art_model.pt"):
    model = WallArtClassifier(input_dim=input_dim)
    model.load_state_dict(torch.load(path))
    model.eval()
    return model    

def main():
    embeddings_pairs, labels = create_embedding_pairs_from_files(
        wall_path="embeddings_cache/wall_embeddings.pkl",
        art_path="embeddings_cache/art_embeddings.pkl"
    )
    X, y = prepare_dataset(embeddings_pairs, labels)
    pairs_list = list(embeddings_pairs.keys())  # "wall,art" strings
    pairs = [(int(p.split(",")[0]), p.split(",")[1]) for p in pairs_list]

    (X_train, y_train), (X_val, y_val) = split_dataset_by_wall(X, y, pairs)

    # Convert to tensors
    train_loader = DataLoader(TensorDataset(
        torch.tensor(X_train, dtype=torch.float32),
        torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
    ), batch_size=64, shuffle=True)

    val_loader = DataLoader(TensorDataset(
        torch.tensor(X_val, dtype=torch.float32),
        torch.tensor(y_val, dtype=torch.float32).unsqueeze(1)
    ), batch_size=64)
    
    model = WallArtClassifier(input_dim=X.shape[1], dropout_rate=0.5)
    print(f"input_dim: {X.shape[1]}")
    trained_model, train_losses, val_losses = train_model(
        model, train_loader, val_loader, epochs=27, lr=0.005, weight_decay=0.0001
    )

    # Save model
    model_filename = f"wall_art_model.pt"
    save_model(trained_model, model_filename)

if __name__ == "__main__":
    main()
