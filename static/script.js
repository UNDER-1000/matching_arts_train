// --- DOM Elements ---
const submitBtn = document.getElementById("submitRatingsBtn");
const filterSelect = document.getElementById("filterSelect");
const sizeSlider = document.getElementById("sizeSlider");
const gallery = document.querySelector(".gallery-container");
const statsLabel = document.getElementById("statsLabel");
const statusLabel = document.querySelector(".status-label");
const saveCheckbox = document.getElementById("savePredictCheckbox");
const apiEndpointInput = document.getElementById("apiEndpoint"); // Get the API endpoint input field
const newIdLabel = document.getElementById("newIdLabel");

// New parameter input elements
const embeddingInput = document.getElementById("embeddingInput");
const colorInput = document.getElementById("colorInput");
const abstractInput = document.getElementById("abstractInput");
const noisyInput = document.getElementById("noisyInput");
const paintInput = document.getElementById("paintInput");

// --- State ---
let allImages = []; // Stores all initial images loaded from /api/images
let currentDisplayedImages = []; // Stores the images currently shown in the gallery (either initial or predicted)
let preferences = {}; // Stores user ratings for images (key: image_id, value: rating)
let thumbnailSize = 150;
let predictionSessionId = null; // To store the session ID from /predict

// --- Initialization ---
window.addEventListener("resize", renderGallery);
submitBtn.addEventListener("click", handleSubmit);
filterSelect.addEventListener("change", renderGallery);
sizeSlider.addEventListener("input", () => {
  thumbnailSize = parseInt(sizeSlider.value, 10);
  renderGallery();
});

loadImages();

// --- Load Images from API ---
async function loadImages() {
  statusLabel.textContent = "Loading images metadata...";
  try {
    const res = await fetch("/api/images");
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const data = await res.json();

    allImages = [...data]; // Store all images initially
    currentDisplayedImages = [...data]; // Initially display all images
    shuffleArray(currentDisplayedImages); // Shuffle for initial display
    preferences = Object.fromEntries(
      currentDisplayedImages.map((img) => [img.id, -1])
    ); // Initialize preferences for all images

    renderGallery();
    updateStats();
    // statusLabel.textContent = `Loaded ${currentDisplayedImages.length} images.`;
    statusLabel.textContent = `Loaded ${currentDisplayedImages.length} image references.`;
  } catch (err) {
    alert(`Error loading images: ${err.message}`);
    statusLabel.textContent = "Failed to load images.";
  }
}

function shuffleArray(array) {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
}

// --- Render Gallery ---
function renderGallery() {
  gallery.innerHTML = "";
  const filteredImages = getFilteredImages();

  if (filteredImages.length === 0) {
    statusLabel.textContent = "No images to display based on current filter.";
    return;
  }

  statusLabel.textContent = `Preparing to render ${filteredImages.length} images...`;

  filteredImages.forEach((img) => {
    const frame = document.createElement("div");
    frame.className = "image-frame";

    const canvas = createCanvas(img);

    const idLabel = document.createElement("div");
    idLabel.textContent = `ID: ${img.id}`;
    idLabel.className = "image-id-label";

    const buttons = createRatingButtons(img.id, canvas);

    frame.appendChild(canvas);
    frame.appendChild(idLabel);
    frame.appendChild(buttons);
    gallery.appendChild(frame);
  });
  statusLabel.textContent = `Displayed ${filteredImages.length} image placeholders. Images will load on scroll.`;
}

// --- Create Canvas Thumbnail ---
function createCanvas(imgData) {
  const canvas = document.createElement("canvas");
  canvas.width = thumbnailSize;
  canvas.height = thumbnailSize;
  updateCanvasBorder(imgData.id, canvas);

  const ctx = canvas.getContext("2d");

  // Draw placeholder
  ctx.fillStyle = "#eee";
  ctx.fillRect(0, 0, thumbnailSize, thumbnailSize);
  ctx.fillStyle = "black";
  ctx.font = "16px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("Loading…", thumbnailSize / 2, thumbnailSize / 2);
  ctx.fillText(`ID: ${imgData.id}`, thumbnailSize / 2, thumbnailSize / 2 + 20);

  // Use IntersectionObserver for lazy loading
  const observer = new IntersectionObserver(
    (entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const img = new Image();
          img.crossOrigin = "anonymous";

          img.onload = () => {
            const imgW = img.naturalWidth || img.width;
            const imgH = img.naturalHeight || img.height;

            if (imgW === 0 || imgH === 0) {
              console.warn(
                `⚠️ Image ${imgData.id} loaded but has zero dimensions.`
              );
              showErrorOnCanvas(ctx, "Empty image");
              return;
            }

            const scale = Math.max(thumbnailSize / imgW, thumbnailSize / imgH);
            const scaledW = imgW * scale;
            const scaledH = imgH * scale;
            const offsetX = (thumbnailSize - scaledW) / 2;
            const offsetY = (thumbnailSize - scaledH) / 2;

            ctx.clearRect(0, 0, thumbnailSize, thumbnailSize);
            ctx.drawImage(img, offsetX, offsetY, scaledW, scaledH);
            observer.unobserve(canvas);
          };

          img.onerror = () => {
            console.error(
              `❌ Failed to load image ${imgData.id}, path: ${imgData.path}`
            );
            showErrorOnCanvas(ctx, "Failed to load");
            observer.unobserve(canvas);
          };

          img.src = imgData.path;
        }
      });
    },
    {
      root: gallery,
      rootMargin: "100px",
      threshold: 0,
    }
  );

  observer.observe(canvas);

  return canvas;
}

// Helper to draw error message
function showErrorOnCanvas(ctx, message) {
  ctx.clearRect(0, 0, thumbnailSize, thumbnailSize);
  ctx.fillStyle = "#fcc";
  ctx.fillRect(0, 0, thumbnailSize, thumbnailSize);
  ctx.fillStyle = "#900";
  ctx.font = "14px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(message, thumbnailSize / 2, thumbnailSize / 2);
}

// --- Create Rating Buttons ---
function createRatingButtons(id, canvas) {
  const container = document.createElement("div");
  container.className = "image-buttons";

  const likeBtn = document.createElement("button");
  likeBtn.textContent = "👍";
  likeBtn.onclick = () => setRating(id, 1, canvas);
  likeBtn.style.backgroundColor = "lightgreen";

  const dislikeBtn = document.createElement("button");
  dislikeBtn.textContent = "👎";
  dislikeBtn.onclick = () => setRating(id, 0, canvas);
  dislikeBtn.style.backgroundColor = "lightcoral";

  const clearBth = document.createElement("button");
  clearBth.textContent = "❓";
  clearBth.onclick = () => setRating(id, -1, canvas);
  clearBth.style.backgroundColor = "lightgray";

  container.appendChild(likeBtn);
  container.appendChild(dislikeBtn);
  container.appendChild(clearBth);
  return container;
}

// --- Set Rating ---
function setRating(id, value, canvas) {
  preferences[id] = value;
  updateCanvasBorder(id, canvas);
  updateStats();
  const filter = filterSelect.value;
  if (filter !== "all") {
    const image = currentDisplayedImages.find((img) => img.id === id);
    if (image && !getFilteredImages().includes(image)) {
      renderGallery();
    }
  }
}

function updateCanvasBorder(id, canvas) {
  if (!canvas || preferences[id] === undefined) {
    return;
  }
  const value = preferences[id];
  if (value === 1) {
    canvas.style.border = "4px solid green";
  } else if (value === 0) {
    canvas.style.border = "4px solid red";
  } else {
    canvas.style.border = "4px solid gray";
  }
}

// --- Filter Images ---
function getFilteredImages() {
  const filter = filterSelect.value;
  return currentDisplayedImages.filter((img) => {
    const val = preferences[img.id];
    return (
      filter === "all" ||
      (filter === "liked" && val === 1) ||
      (filter === "disliked" && val === 0) ||
      (filter === "unrated" && val === -1)
    );
  });
}

// --- Update Stats ---
function updateStats() {
  const counts = { liked: 0, disliked: 0, unrated: 0 };
  Object.values(preferences).forEach((val) => {
    if (val === 1) counts.liked++;
    else if (val === 0) counts.disliked++;
    else counts.unrated++;
  });

  statsLabel.textContent = `Images: ${currentDisplayedImages.length} | 👍: ${counts.liked} | 👎: ${counts.disliked} | ❓: ${counts.unrated}`;
}

// --- Submit Ratings and Get Prediction / Submit Feedback ---
async function handleSubmit() {
  if (predictionSessionId) {
    await submitFeedback();
  } else {
    await submitInitialRatings();
  }
}

async function submitInitialRatings() {
  const ratedImageIds = Object.keys(preferences).filter(
    (id) => preferences[id] !== -1
  );
  const targets = ratedImageIds.map((id) => preferences[id]);

  // Retrieve values from the new input fields
  const embedding = parseFloat(embeddingInput.value);
  const color = parseFloat(colorInput.value);
  const abstract = parseFloat(abstractInput.value);
  const noisy = parseFloat(noisyInput.value);
  const paint = parseFloat(paintInput.value);

  const unratedCount = Object.values(preferences).filter(
    (val) => val === -1
  ).length;
  if (
    unratedCount > 0 &&
    !confirm(`There are ${unratedCount} unrated images. Submit anyway?`)
  ) {
    return;
  }

  statusLabel.textContent =
    "Submitting initial ratings and getting predictions...";
  try {
    const predictEndpoint = apiEndpointInput.value;
    const res = await fetch(predictEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        image_ids: ratedImageIds.map(Number),
        target: targets,
        // Include the new parameters
        embedding: embedding,
        color: color,
        abstract: abstract,
        noisy: noisy,
        paint: paint,
      }),
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`${res.status} ${res.statusText}: ${errorText}`);
    }
    const responseData = await res.json();
    const predictedIds = responseData.predicted_ids;

    if (!Array.isArray(predictedIds)) {
      throw new Error(
        "Server response did not contain a valid 'predicted_ids' array."
      );
    }

    predictionSessionId = responseData.session_id;

    currentDisplayedImages = allImages.filter((img) =>
      predictedIds.includes(img.id)
    );
    preferences = Object.fromEntries(
      currentDisplayedImages.map((img) => [img.id, -1])
    );

    renderGallery();
    updateStats();
    statusLabel.textContent = `Prediction received. Showing top ${currentDisplayedImages.length} images. Please rate them.`;
    submitBtn.textContent = "Submit Feedback";
    if (responseData.new_id !== undefined) {
      newIdLabel.textContent = responseData.new_id;
    } else {
      newIdLabel.textContent = "None";
    }
  } catch (err) {
    alert(`Prediction error: ${err.message}`);
    statusLabel.textContent = "Prediction failed.";
  }
}

async function submitFeedback() {
  if (!predictionSessionId) {
    alert("No active prediction session to submit feedback for.");
    return;
  }

  const feedbackData = {};
  currentDisplayedImages.forEach((img) => {
    feedbackData[img.id] =
      preferences[img.id] !== undefined ? preferences[img.id] : -1;
  });

  statusLabel.textContent = "Submitting feedback on predicted images...";
  try {
    const res = await fetch("/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prediction_session_id: predictionSessionId,
        feedback: feedbackData,
      }),
    });

    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const response = await res.json();
    alert(response.message);

    predictionSessionId = null;
    newIdLabel.textContent = "None";
    loadImages();
    submitBtn.textContent = "Submit Ratings";
    statusLabel.textContent = "Feedback submitted. Ready for new ratings.";
  } catch (err) {
    alert(`Feedback submission error: ${err.message}`);
    statusLabel.textContent = "Feedback submission failed.";
  }
}
