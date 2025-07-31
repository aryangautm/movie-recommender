
import React, { useState, useEffect, useRef } from 'react';
import { MovieIcon, TVShowIcon } from './icons';

export type ContentType = 'movie' | 'tvShow';

const CONTENT_TYPES = [
  { id: 'movie' as ContentType, label: 'Movies', icon: <MovieIcon className="h-5 w-5" /> },
  { id: 'tvShow' as ContentType, label: 'TV Shows', icon: <TVShowIcon className="h-5 w-5" /> },
];

interface ContentTypeToggleProps {
  activeType: ContentType;
  onTypeChange: (type: ContentType) => void;
}

const ContentTypeToggle: React.FC<ContentTypeToggleProps> = ({ activeType, onTypeChange }) => {
  const [showBubble, setShowBubble] = useState(false);
  const bubbleTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    // Cleanup timeout on unmount to prevent memory leaks
    return () => {
      if (bubbleTimeoutRef.current) {
        clearTimeout(bubbleTimeoutRef.current);
      }
    };
  }, []);

  const handleButtonClick = (id: ContentType) => {
    if (id === 'tvShow') {
      // If the bubble is already showing, do nothing.
      if (showBubble) return;

      // Show the bubble and set a timer to hide it.
      setShowBubble(true);
      bubbleTimeoutRef.current = window.setTimeout(() => {
        setShowBubble(false);
      }, 2000); // Bubble is visible for 2 seconds.
    } else {
      // For 'movie', call the passed-in handler.
      onTypeChange(id);
    }
  };

  return (
    <div className="relative w-fit">
      {/* "Coming Soon!" bubble message */}
      <div
        className={`absolute bottom-full right-0 mb-2 w-max px-3 py-1.5 text-sm font-semibold text-gray-800 bg-gray-200 rounded-lg shadow-lg transition-all duration-300 ease-in-out transform
          ${showBubble ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2 pointer-events-none'}`}
        role="status"
        aria-live="polite"
      >
        Coming Soon!
        <div className="absolute left-1/2 -translate-x-1/2 top-full h-0 w-0 border-x-4 border-x-transparent border-t-4 border-t-gray-200" />
      </div>

      <div className="flex gap-2 p-1 bg-[#1c1917]/50 border border-white/10 rounded-xl">
        {CONTENT_TYPES.map(({ id, label, icon }) => (
          <button
            key={id}
            onClick={() => handleButtonClick(id)}
            className={`flex items-center justify-center gap-2 py-2 px-4 rounded-lg transition-all duration-300 text-sm font-medium
              ${activeType === id
                ? 'bg-gray-200 text-black shadow-md'
                : 'text-gray-300 hover:bg-white/10'
              }
            `}
          >
            {icon}
            {label}
          </button>
        ))}
      </div>
    </div>
  );
};

export default ContentTypeToggle;
