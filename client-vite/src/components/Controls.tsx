interface ControlsProps {
  thumbnailSize: number;
  onSizeChange: (size: number) => void;
  onSubmit: () => void;
  onFilterChange: (filter: string) => void;
  filter: string;
  isSubmitting: boolean;
  weights: {
    embedding: number;
    color: number;
    abstract: number;
    noisy: number;
    paint: number;
  };
  onWeightChange: (name: string, value: number) => void;
}

export default function Controls({ 
  thumbnailSize, 
  onSizeChange, 
  onSubmit,
  onFilterChange,
  filter,
  isSubmitting,
  weights,
  onWeightChange
}: ControlsProps) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
        <div className="flex items-center gap-2">
          <label htmlFor="sizeSlider" className="text-sm font-medium">
            Thumbnail Size:
          </label>
          <input
            id="sizeSlider"
            type="range"
            min="100"
            max="300"
            step="10"
            value={thumbnailSize}
            onChange={(e) => onSizeChange(parseInt(e.target.value, 10))}
            className="w-32"
            disabled={isSubmitting}
          />
          <span className="text-sm text-gray-600">{thumbnailSize}px</span>
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="filterSelect" className="text-sm font-medium">
            Filter:
          </label>
          <select
            id="filterSelect"
            value={filter}
            onChange={(e) => onFilterChange(e.target.value)}
            className="rounded border border-gray-300 px-2 py-1 text-sm"
            disabled={isSubmitting}
          >
            <option value="all">All Images</option>
            <option value="liked">Liked</option>
            <option value="disliked">Disliked</option>
            <option value="unrated">Unrated</option>
          </select>
        </div>

        <button
          onClick={onSubmit}
          disabled={isSubmitting}
          className={`px-4 py-2 rounded transition-colors ${
            isSubmitting
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-500 hover:bg-blue-600 text-white'
          }`}
        >
          {isSubmitting ? 'Submitting...' : 'Submit Ratings'}
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
        <div className="flex flex-col gap-1">
          <label htmlFor="embedding" className="text-sm font-medium">
            Embedding Weight
          </label>
          <input
            id="embedding"
            type="number"
            min="0"
            max="1"
            step="0.1"
            value={weights.embedding}
            onChange={(e) => onWeightChange('embedding', parseFloat(e.target.value))}
            className="rounded border border-gray-300 px-2 py-1"
            disabled={isSubmitting}
          />
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="color" className="text-sm font-medium">
            Color Weight
          </label>
          <input
            id="color"
            type="number"
            min="0"
            max="1"
            step="0.1"
            value={weights.color}
            onChange={(e) => onWeightChange('color', parseFloat(e.target.value))}
            className="rounded border border-gray-300 px-2 py-1"
            disabled={isSubmitting}
          />
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="abstract" className="text-sm font-medium">
            Abstract Weight
          </label>
          <input
            id="abstract"
            type="number"
            min="0"
            max="1"
            step="0.1"
            value={weights.abstract}
            onChange={(e) => onWeightChange('abstract', parseFloat(e.target.value))}
            className="rounded border border-gray-300 px-2 py-1"
            disabled={isSubmitting}
          />
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="noisy" className="text-sm font-medium">
            Noisy Weight
          </label>
          <input
            id="noisy"
            type="number"
            min="0"
            max="1"
            step="0.1"
            value={weights.noisy}
            onChange={(e) => onWeightChange('noisy', parseFloat(e.target.value))}
            className="rounded border border-gray-300 px-2 py-1"
            disabled={isSubmitting}
          />
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="paint" className="text-sm font-medium">
            Paint Weight
          </label>
          <input
            id="paint"
            type="number"
            min="0"
            max="1"
            step="0.1"
            value={weights.paint}
            onChange={(e) => onWeightChange('paint', parseFloat(e.target.value))}
            className="rounded border border-gray-300 px-2 py-1"
            disabled={isSubmitting}
          />
        </div>
      </div>
    </div>
  );
} 