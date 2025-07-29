
import React from 'react';
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
  return (
    <div className="flex w-fit gap-2 p-1 bg-[#1c1917]/50 border border-white/10 rounded-xl">
      {CONTENT_TYPES.map(({ id, label, icon }) => (
        <button
          key={id}
          onClick={() => onTypeChange(id)}
          className={`flex items-center justify-center gap-2 py-2 px-4 rounded-lg transition-all duration-300 text-sm font-medium
            ${activeType === id 
              ? 'bg-gray-200 text-black shadow-md' 
              : 'text-gray-300 hover:bg-white/10'
            }`}
        >
          {icon}
          {label}
        </button>
      ))}
    </div>
  );
};

export default ContentTypeToggle;
