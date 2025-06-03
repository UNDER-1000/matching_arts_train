import { useState, useEffect } from 'react';
import ImageGallery from './components/ImageGallery';
import Controls from './components/Controls';
import ErrorBoundary from './components/ErrorBoundary';
import type { ImageInfo } from './types';

function App() {
  const [images, setImages] = useState<ImageInfo[]>([]);
  const [currentDisplayedImages, setCurrentDisplayedImages] = useState<ImageInfo[]>([]);
  const [preferences, setPreferences] = useState<Record<number, number>>({});
  const [thumbnailSize, setThumbnailSize] = useState(150);
  // const [predictionSessionId, setPredictionSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState('Loading...');
  const [filter, setFilter] = useState('all');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [weights, setWeights] = useState({
    embedding: 1,
    color: 1,
    abstract: 1,
    noisy: 1,
    paint: 1
  });

  useEffect(() => {
    loadImages();
  }, []);

  const loadImages = async () => {
    setStatus('Loading images metadata...');
    try {
      const response = await fetch('/api/images');
      if (!response.ok) {
        throw new Error('Failed to load images');
      }
      const data = await response.json();
      setImages(data);
      setCurrentDisplayedImages(shuffleArray([...data]));
      setPreferences(Object.fromEntries(data.map((img: ImageInfo) => [img.id, -1])));
      setStatus(`Loaded ${data.length} image references.`);
    } catch (error) {
      console.error('Error loading images:', error);
      setStatus('Error loading images. Please try again.');
    }
  };

  const shuffleArray = (array: ImageInfo[]) => {
    const newArray = [...array];
    for (let i = newArray.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [newArray[i], newArray[j]] = [newArray[j], newArray[i]];
    }
    return newArray;
  };

  const handleRating = (id: number, value: number) => {
    setPreferences(prev => ({
      ...prev,
      [id]: value
    }));
  };

  const handleWeightChange = (name: string, value: number) => {
    setWeights(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleFilterChange = (newFilter: string) => {
    setFilter(newFilter);
    const filteredImages = images.filter(img => {
      const rating = preferences[img.id];
      return (
        newFilter === 'all' ||
        (newFilter === 'liked' && rating === 1) ||
        (newFilter === 'disliked' && rating === 0) ||
        (newFilter === 'unrated' && rating === -1)
      );
    });
    setCurrentDisplayedImages(filteredImages);
  };

  const handleSubmit = async () => {
    // Get only rated images (where rating is not -1)
    const ratedImages = Object.entries(preferences)
      .filter(([_, rating]) => rating !== -1)
      .map(([id, rating]) => ({
        id: parseInt(id),
        rating
      }));

    if (ratedImages.length === 0) {
      setStatus('Please rate at least one image before submitting.');
      return;
    }

    setIsSubmitting(true);
    setStatus('Submitting ratings...');

    try {
      const response = await fetch('/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_ids: ratedImages.map(img => img.id),
          target: ratedImages.map(img => img.rating),
          ...weights
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit ratings');
      }

      const data = await response.json();
      // setPredictionSessionId(data.session_id);
      
      // Update displayed images with predictions
      const predictedImages = images.filter(img => 
        data.predicted_ids.includes(img.id)
      );
      setCurrentDisplayedImages(predictedImages);
      setStatus(`Showing ${predictedImages.length} predicted images. Please rate them.`);
    } catch (error) {
      console.error('Error submitting ratings:', error);
      setStatus('Error submitting ratings. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // const handleFeedback = async (feedback: Record<number, number>) => {
  //   if (!predictionSessionId) return;

  //   try {
  //     const response = await fetch('/feedback', {
  //       method: 'POST',
  //       headers: {
  //         'Content-Type': 'application/json',
  //       },
  //       body: JSON.stringify({
  //         prediction_session_id: predictionSessionId,
  //         feedback,
  //       }),
  //     });

  //     if (!response.ok) {
  //       throw new Error('Failed to submit feedback');
  //     }

  //     setStatus('Feedback submitted successfully!');
  //   } catch (error) {
  //     console.error('Error submitting feedback:', error);
  //     setStatus('Error submitting feedback. Please try again.');
  //   }
  // };

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Image Matching System</h1>
        
        <Controls 
          thumbnailSize={thumbnailSize}
          onSizeChange={setThumbnailSize}
          onSubmit={handleSubmit}
          onFilterChange={handleFilterChange}
          filter={filter}
          isSubmitting={isSubmitting}
          weights={weights}
          onWeightChange={handleWeightChange}
        />

        <div className="mt-4 text-gray-600">{status}</div>

        <ErrorBoundary>
          <ImageGallery
            images={currentDisplayedImages}
            preferences={preferences}
            thumbnailSize={thumbnailSize}
            onRating={handleRating}
          />
        </ErrorBoundary>
      </div>
    </main>
  );
}

export default App;
