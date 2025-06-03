import { useEffect, useRef, useState } from 'react';
import type { ImageInfo } from '../types';

interface ImageGalleryProps {
  images: ImageInfo[];
  preferences: Record<number, number>;
  thumbnailSize: number;
  onRating: (id: number, value: number) => void;
}

export default function ImageGallery({ images, preferences, thumbnailSize, onRating }: ImageGalleryProps) {
  const galleryRef = useRef<HTMLDivElement>(null);
  const [loadingStates, setLoadingStates] = useState<Record<number, 'loading' | 'loaded' | 'error'>>({});

  useEffect(() => {
    // Initialize loading states for all images
    const initialStates = images.reduce((acc, img) => ({
      ...acc,
      [img.id]: 'loading'
    }), {});
    setLoadingStates(initialStates);

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const img = entry.target as HTMLImageElement;
            const imageId = img.dataset.id;
            if (imageId && img.dataset.src) {
              img.src = img.dataset.src;
              observer.unobserve(img);
            }
          }
        });
      },
      {
        root: galleryRef.current,
        rootMargin: '200px',
        threshold: 0,
      }
    );

    // Observe all images that are not yet loaded
    const imageElements = galleryRef.current?.querySelectorAll('img[data-src]');
    imageElements?.forEach((img) => observer.observe(img));

    return () => observer.disconnect();
  }, [images]);

  const handleImageLoad = (id: number) => {
    setLoadingStates(prev => ({
      ...prev,
      [id]: 'loaded'
    }));
  };

  const handleImageError = (id: number) => {
    setLoadingStates(prev => ({
      ...prev,
      [id]: 'error'
    }));
  };

  return (
    <div 
      ref={galleryRef}
      className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 mt-8"
    >
      {images.map((img) => (
        <div 
          key={img.id}
          className="flex flex-col items-center gap-2"
        >
          <div 
            className="relative"
            style={{ width: thumbnailSize, height: thumbnailSize }}
          >
            {loadingStates[img.id] === 'error' ? (
              <div 
                className="w-full h-full flex items-center justify-center bg-red-50 border-4 border-red-200 rounded"
              >
                <span className="text-red-500 text-sm">Failed to load</span>
              </div>
            ) : (
              <div className="relative w-full h-full">
                {loadingStates[img.id] === 'loading' && (
                  <div 
                    className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded animate-pulse"
                  >
                    <span className="text-gray-400 text-sm">Loading...</span>
                  </div>
                )}
                <img
                  data-src={`/images/${img.name}`}
                  data-id={img.id}
                  alt={`Image ${img.id}`}
                  className={`w-full h-full object-cover transition-opacity duration-300 ${
                    loadingStates[img.id] === 'loaded' ? 'opacity-100' : 'opacity-0'
                  }`}
                  style={{
                    borderColor: preferences[img.id] === 1 
                      ? 'green' 
                      : preferences[img.id] === 0 
                        ? 'red' 
                        : 'gray'
                  }}
                  onLoad={() => handleImageLoad(img.id)}
                  onError={() => handleImageError(img.id)}
                />
              </div>
            )}
          </div>
          
          <div className="text-sm text-gray-600">ID: {img.id}</div>
          
          <div className="flex gap-2">
            <button
              onClick={() => onRating(img.id, 1)}
              className={`px-3 py-1 rounded transition-colors ${
                preferences[img.id] === 1 
                  ? 'bg-green-500 text-white' 
                  : 'bg-green-100 hover:bg-green-200'
              }`}
            >
              👍
            </button>
            <button
              onClick={() => onRating(img.id, 0)}
              className={`px-3 py-1 rounded transition-colors ${
                preferences[img.id] === 0 
                  ? 'bg-red-500 text-white' 
                  : 'bg-red-100 hover:bg-red-200'
              }`}
            >
              👎
            </button>
            <button
              onClick={() => onRating(img.id, -1)}
              className={`px-3 py-1 rounded transition-colors ${
                preferences[img.id] === -1 
                  ? 'bg-gray-500 text-white' 
                  : 'bg-gray-100 hover:bg-gray-200'
              }`}
            >
              ❓
            </button>
          </div>
        </div>
      ))}
    </div>
  );
} 