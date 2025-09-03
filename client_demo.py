import requests
import json
import os # Added for file system operations
import uuid # Added for generating unique IDs
from datetime import datetime
import time
import random

from src.config import Config

# --- Configuration ---
BASE_URL = "http://localhost:8000"
IMAGE_FOLDER_CLIENT = "https://storage.googleapis.com/image-matcher/artworks" # Path to your image folder relative to where client runs
VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')

# --- Helper Functions for API Interaction ---

def add_artwork(artwork_data: dict):
    """
    Calls the /add-artwork endpoint to add a single artwork.
    """
    print(f"\n--- Adding artwork: {artwork_data.get('artwork_name')} ---")
    url = f"{BASE_URL}/add-artwork"
    response = None
    try:
        response = requests.post(url, json=artwork_data)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()
        print("Artwork added successfully:")
        print(json.dumps(data, indent=2))
        return True # Indicate success
    except requests.exceptions.RequestException as e:
        print(f"Error adding artwork: {e}")
        if response is not None:
            print(f"Response status: {response.status_code}")
            print(f"Response detail: {response.text}")
        return False # Indicate failure

def user_interaction(user_id: str, artwork_id: str, action: str):
    """
    Calls the /user-interaction endpoint to simulate a user's action.
    """
    print(f"\n--- User '{user_id}' performing '{action}' on artwork '{artwork_id}' ---")
    url = f"{BASE_URL}/user-interaction"
    interaction_data = {
        "user_id": user_id,
        "artwork_id": artwork_id,
        "action": action,
        "timestamp": datetime.now().isoformat()
    }
    try:
        response = requests.post(url, json=interaction_data)
        response.raise_for_status()
        data = response.json()
        print("Recommendations received:")
        print(json.dumps(data, indent=2))
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error during user interaction: {e}")
        if response is not None:
            print(f"Response status: {response.status_code}")
            print(f"Response detail: {response.text}")
        return []

# --- New client-side function to populate artworks ---
def populate_artworks_from_folder(limit: int = 15):
    """
    Reads image files from a local folder, constructs Artwork data,
    and sends individual POST requests to the /add-artwork endpoint.
    Generates consistent, non-'garbage' dummy data for missing fields.
    """
    print(f"\n--- Populating artworks from '{IMAGE_FOLDER_CLIENT}' (limit={limit}) ---")
    
    loaded_ids = []
    count = 0

    # if not os.path.exists(IMAGE_FOLDER_CLIENT):
    #     print(f"Error: Image folder '{IMAGE_FOLDER_CLIENT}' not found.")
    #     return []

    # for root, _, files in os.walk(IMAGE_FOLDER_CLIENT):
    for idx in range(1, limit + 1):
        filename = f"{idx}.jpg"  # Simulating artwork files
    # for filename in sorted(files):
        if filename.lower().endswith(VALID_EXTENSIONS):
            if count >= limit:
                break

            # Generate a unique ID (can be based on filename or a UUID)
            artwork_id = os.path.splitext(filename)[0] + "-" + str(uuid.uuid4())[:4]
            artwork_name = os.path.splitext(filename)[0].replace('_', ' ').title()
            
            # Consistent (non-'garbage') dummy data
            artist_name = f"Artist_{random.choice(['A', 'B', 'C'])}"
            description = f"A beautiful piece named '{artwork_name}' by {artist_name}, digitally imported."
            category = random.choice(["Abstract", "Portrait", "Landscape", "Still Life"])
            style = random.choice(["Modern", "Impressionist", "Surreal", "Realistic"])
            subject = random.choice(["Nature", "People", "Objects", "Emotions"])
            
            artwork_data = {
                "artwork_id": artwork_id,
                "artist_id": f"artst-{hash(artist_name) % 1000}", # Simple hash for artist ID
                "artist_name": artist_name,
                "artwork_name": artwork_name,
                # Assuming /images endpoint on server serves images from data/data
                "images": [f"{IMAGE_FOLDER_CLIENT}/{filename}"], 
                "description": description,
                "category": category,
                "properties": {"source": "local_folder_import", "client_generated": True},
                "media": "Digital File",
                "medium": "Mixed Media",
                "size": "Digital",
                "price": round(random.uniform(100.0, 5000.0), 2), # Random price
                "styles": [style],
                "subject": subject
            }

            if add_artwork(artwork_data): # Use the existing add_artwork helper to send
                loaded_ids.append(artwork_id)
                count += 1
            
            time.sleep(0.1) # Small delay to not overwhelm the server

            # if count >= limit:
            #     break
        if count >= limit:
            break
            
    print(f"\nSuccessfully populated {len(loaded_ids)} artworks via individual API calls.")
    return loaded_ids

def wall_interaction(user_id: str, wall_index: int):
    """
    Calls the /user-interaction endpoint with action='wall'
    to simulate a wall selection.
    """
    print(f"\n--- User '{user_id}' requesting wall '{wall_index}' ---")
    url = f"{BASE_URL}/user-interaction"
    interaction_data = {
        "user_id": user_id,
        "artwork_id": f"{Config.walls_url}{wall_index}.jpg",  # wall index sent as artwork_id
        "action": "wall",
        "timestamp": datetime.now().isoformat()
    }
    try:
        response = requests.post(url, json=interaction_data)
        response.raise_for_status()
        data = response.json()
        print("Wall recommendations received:")
        print(json.dumps(data, indent=2))
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error during wall interaction: {e}")
        if response is not None:
            print(f"Response status: {response.status_code}")
            print(f"Response detail: {response.text}")
        return []
    
def delete_artwork(artwork_id: str):
    """
    Calls the /delete-artwork/{artwork_id} endpoint.
    """
    print(f"\n--- Deleting artwork '{artwork_id}' ---")
    url = f"{BASE_URL}/delete-artwork/{artwork_id}"
    try:
        response = requests.delete(url)
        response.raise_for_status()
        data = response.json()
        print("Delete response:")
        print(json.dumps(data, indent=2))
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error deleting artwork: {e}")
        if response is not None:
            print(f"Response status: {response.status_code}")
            print(f"Response detail: {response.text}")
        return None


def delete_by_artist(artist_id: str):
    """
    Calls the /delete-by-artist/{artist_id} endpoint.
    """
    print(f"\n--- Deleting all artworks by artist '{artist_id}' ---")
    url = f"{BASE_URL}/delete-by-artist/{artist_id}"
    try:
        response = requests.delete(url)
        response.raise_for_status()
        data = response.json()
        print("Delete by artist response:")
        print(json.dumps(data, indent=2))
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error deleting by artist: {e}")
        if response is not None:
            print(f"Response status: {response.status_code}")
            print(f"Response detail: {response.text}")
        return None

# --- Demo Client Logic ---
if __name__ == "__main__":
    print("Starting FastAPI Demo Client...")

    # 1. Populate initial artworks by sending individual requests from the client
    # This now scans your local 'data/data' folder and sends each artwork.
    all_artwork_ids_in_system = populate_artworks_from_folder(limit=15)

    # 3. Simulate user interactions
    user1_id = "user_alpha"
    user2_id = "user_beta"

    if all_artwork_ids_in_system:
        # User 1 likes a random artwork from the loaded ones
        artwork_to_like = random.choice(all_artwork_ids_in_system)
        user_interaction(user1_id, artwork_to_like, "like")
        time.sleep(1)

        # User 1 dislikes another random artwork
        artwork_to_dislike = random.choice(all_artwork_ids_in_system)
        user_interaction(user1_id, artwork_to_dislike, "dislike")
        time.sleep(1)

        # User 2 likes the custom artwork
        user_interaction(user2_id, all_artwork_ids_in_system[0], "like")
        time.sleep(1)

        # User 2 likes another artwork
        another_artwork_for_user2 = random.choice(all_artwork_ids_in_system[1])
        user_interaction(user2_id, another_artwork_for_user2, "like")

        # 3. Simulate wall selection (random wall index 1–100)
    wall_index = random.randint(1, 100)
    wall_result = wall_interaction(user1_id, wall_index)
    if wall_result:
        print(f"Recommended artworks for wall {wall_index}: {wall_result}")

        # 4. Demo deleting
    if all_artwork_ids_in_system:
        # Delete a single artwork
        delete_artwork(all_artwork_ids_in_system[0])

        # Delete by artist (using the same artist_id as first artwork)
        # You can extract artist_id from how you generated it in populate_artworks_from_folder
        sample_artist_id = f"artst-{hash('Artist_A') % 1000}"  # example if first was Artist_A
        delete_by_artist(sample_artist_id)

    print("\nDemo client finished.")