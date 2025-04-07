🖼️ Project Overview

This project allows users to provide feedback (like/dislike) on images, and trains models to predict preferences based on CLIP embeddings and color features, and 3 classifiers [noise, abstract, paint].

✅ Workflow
1.	Input:
*   Three predefined categories: noise, abstract, paint.
*	A list of image_ids (which correspond to filenames in a directory).
*	A list of labels (1 = like, 0 = dislike) corresponding to each image. 
2.  Feature Extraction:
*	Extract CLIP embeddings and color features separately.
3.  Model Training:
	*	Train models on embeddings and colors.
	*	Generate 5 prediction scores per image (from various models - [embeddings, color, noise, abstract, paint]).
	*	Train a final classifier on these 5 scores to make the final prediction.
4.	Data Handling:
   *	Uses Polars DataFrames and NumPy for efficient processing.
   *	A CSV file is used to persist the feature and label data.

🛠️ Structure
*	main.py: FastAPI server entry point.
*	logic.py: Orchestrates the training and prediction pipeline.
*	features.py: Used when performing a full restart (rebuilds features from scratch).
*	classifiers_api.py, colors_api.py, embeddings_api.py: Handle prediction of individual models; used during restarts.
*	config.py: Contains configurable constants (e.g., paths, folders).
*	show.ipynb: Jupyter Notebook to visualize image preferences and model predictions.

🚀 Running the Server

Make sure uv is installed, then run:

uv run main.py

Visit the interactive API docs at:
👉 http://127.0.0.1:8000/docs

🔁 Restart Option

Use the restart mode only the first time (or when rebuilding from scratch). It regenerates the CSV.

