const apiEndpointInput = document.getElementById("apiEndpoint");
const submitRatingsBtn = document.getElementById("submitRatingsBtn");
const newIdLabel = document.getElementById("newIdLabel");
const filterSelect = document.getElementById("filterSelect");
const sizeSlider = document.getElementById("sizeSlider");
const galleryContainer = document.querySelector(".gallery-container");
const statsLabel = document.getElementById("statsLabel");
const statusLabel = document.querySelector(".status-label");

let images = []; // Array to hold image data (path, name, id, preference)
let allImages = []; // Keep a copy of all loaded images
let preferences = {}; // Object to store image preferences (id: -1|0|1)
let thumbnailSize = 150;
let columns = 0; // Will be determined dynamically

async function loadImages() {
  statusLabel.textContent = "Loading images...";
  try {
    const response = await fetch("http://localhost:8000/api/images"); // Use the full URL of your backend
    if (response.ok) {
      const data = await response.json();
      images = data;
      allImages = [...data]; // Create a copy of all loaded images
      images.forEach((img) => (preferences[img.id] = -1));
      displayGallery();
      updateStats();
      statusLabel.textContent = `Loaded ${images.length} images`;
    } else {
      alert(
        `Failed to load images: ${response.status} - ${response.statusText}`
      );
      statusLabel.textContent = "Error loading images";
    }
  } catch (error) {
    alert(`Failed to connect to the image API: ${error}`);
    statusLabel.textContent = "Error connecting to API";
  }
}

function displayGallery() {
  galleryContainer.innerHTML = ""; // Clear the current gallery
  const filteredImages = getFilteredImages();
  columns = Math.floor(galleryContainer.offsetWidth / (thumbnailSize + 20)); // Adjust for margin/padding

  filteredImages.forEach((image) => {
    const frame = document.createElement("div");
    frame.classList.add("image-frame");

    const canvas = document.createElement("canvas");
    canvas.width = thumbnailSize;
    canvas.height = thumbnailSize;
    canvas.style.border = "4px solid gray"; // Default border

    const img = new Image();
    img.onload = () => {
      const ctx = canvas.getContext("2d");
      const ratio = Math.min(
        thumbnailSize / img.width,
        thumbnailSize / img.height
      );
      const newWidth = img.width * ratio;
      const newHeight = img.height * ratio;
      const offsetX = (thumbnailSize - newWidth) / 2;
      const offsetY = (thumbnailSize - newHeight) / 2;
      ctx.drawImage(img, offsetX, offsetY, newWidth, newHeight);
    };
    // IMPORTANT: Construct the full URL to your FastAPI backend's image route
    img.src = `http://localhost:8000${image.path}`; // image.path is something like /images/13947.jpg

    frame.appendChild(canvas);
    const idLabel = document.createElement("div");
    idLabel.textContent = `ID: ${image.id}`;
    frame.appendChild(idLabel);

    const buttonsDiv = document.createElement("div");
    buttonsDiv.classList.add("image-buttons");
    const likeBtn = document.createElement("button");
    likeBtn.textContent = "👍";
    likeBtn.addEventListener("click", () => setPreference(image.id, 1, canvas));
    const dislikeBtn = document.createElement("button");
    dislikeBtn.textContent = "👎";
    dislikeBtn.addEventListener("click", () =>
      setPreference(image.id, 0, canvas)
    );
    buttonsDiv.appendChild(likeBtn);
    buttonsDiv.appendChild(dislikeBtn);
    frame.appendChild(buttonsDiv);

    galleryContainer.appendChild(frame);
  });
}

function getFilteredImages() {
  const filterValue = filterSelect.value;
  return images.filter((img) => {
    const pref = preferences[img.id];
    if (filterValue === "all") return true;
    if (filterValue === "liked") return pref === 1;
    if (filterValue === "disliked") return pref === 0;
    if (filterValue === "unrated") return pref === -1;
    return true;
  });
}

function setPreference(imgId, value, canvasElement) {
  preferences[imgId] = value;
  canvasElement.style.borderColor =
    value === 1 ? "green" : value === 0 ? "red" : "gray";
  updateStats();
}

function updateStats() {
  const likedCount = Object.values(preferences).filter((p) => p === 1).length;
  const dislikedCount = Object.values(preferences).filter(
    (p) => p === 0
  ).length;
  const unratedCount = Object.values(preferences).filter(
    (p) => p === -1
  ).length;
  statsLabel.textContent = `Images: ${allImages.length} | Liked: ${likedCount} | Disliked: ${dislikedCount} | Unrated: ${unratedCount}`;
}

sizeSlider.addEventListener("input", () => {
  thumbnailSize = parseInt(sizeSlider.value);
  displayGallery();
});

filterSelect.addEventListener("change", displayGallery);

submitRatingsBtn.addEventListener("click", async () => {
  const endpoint = "http://localhost:8000/predict"; // Hardcode the predict endpoint for simplicity

  const ratedImages = Object.keys(preferences).filter(
    (id) => preferences[id] !== -1
  );
  const imageIdsToSend = ratedImages.map((id) => parseInt(id));
  const targetsToSend = imageIdsToSend.map((id) => preferences[id]);

  const unratedCount = Object.values(preferences).filter(
    (p) => p === -1
  ).length;
  if (
    unratedCount > 0 &&
    !confirm(`There are ${unratedCount} unrated images. Submit anyway?`)
  ) {
    return;
  }

  statusLabel.textContent = "Submitting ratings and getting predictions...";
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        image_ids: imageIdsToSend,
        target: targetsToSend,
      }),
    });

    if (response.ok) {
      const predictedIds = await response.json();
      statusLabel.textContent = `Prediction received. Displaying top ${predictedIds.length} images.`;

      // Filter the 'allImages' array to only include the predicted IDs
      images = allImages.filter((image) => predictedIds.includes(image.id));

      // Ensure we only take the first 10 (though the server should handle this)
      images = images.slice(0, 10);

      preferences = {}; // Reset preferences for the new set of images
      images.forEach((img) => (preferences[img.id] = -1)); // Reset preferences for the new images
      displayGallery(); // Re-render the gallery with the top 10 images
      updateStats(); // Update the stats based on the new set of images
    } else {
      alert(
        `Failed to get prediction: ${response.status} - ${response.statusText}`
      );
      statusLabel.textContent = "Prediction failed.";
    }
  } catch (error) {
    alert(`Failed to connect to API: ${error}`);
    statusLabel.textContent = "Error during submission.";
  } finally {
    statusLabel.textContent = "Ready";
  }
});

// Load images when the page loads
loadImages();

// Basic responsiveness for the gallery layout
function updateGalleryLayout() {
  columns = Math.floor(galleryContainer.offsetWidth / (thumbnailSize + 20));
  displayGallery(); // Re-render the gallery to adjust the layout
}

window.addEventListener("resize", updateGalleryLayout);
