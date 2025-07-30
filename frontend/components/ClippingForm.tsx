
import React, { useState, useEffect } from 'react';
import { ArrowRightIcon, SpinnerIcon } from './icons';
import ContentTypeToggle, { ContentType } from './ContentTypeToggle';

const PLACEHOLDER_TEXTS = [
  "The Shawshank Redemption",
  "The Godfather",
  "Breaking Bad",
  "The Dark Knight",
  "Pulp Fiction",
  "Forrest Gump",
  "Inception",
  "Game of Thrones",
  "Stranger Things",
];

interface ClippingFormProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  isLoading: boolean;
}

const ClippingForm: React.FC<ClippingFormProps> = ({ searchQuery, setSearchQuery, isLoading }) => {
  const [activeContentType, setActiveContentType] = useState<ContentType>('movie');
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const [animationClass, setAnimationClass] = useState('animate-placeholder-in');
  const [isInputFocused, setIsInputFocused] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setAnimationClass('animate-placeholder-out');

      setTimeout(() => {
        setPlaceholderIndex(prevIndex => (prevIndex + 1) % PLACEHOLDER_TEXTS.length);
        setAnimationClass('animate-placeholder-in');
      }, 500); // Corresponds to animation duration
    }, 3000);

    return () => clearInterval(interval);
  }, []);


  return (
    <div className="w-full max-w-xl lg:max-w-2xl bg-[#1C1C1E]/80 backdrop-blur-xl border border-white/10 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6">
      
      {/* Search Input */}
      <div className="relative">
        <input
          type="text"
          placeholder=""
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onFocus={() => setIsInputFocused(true)}
          onBlur={() => setIsInputFocused(false)}
          className="w-full bg-[#1c1917]/50 border border-white/10 rounded-lg py-3 pl-4 pr-12 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition-all duration-300 text-white"
        />
        {/* Animated Placeholder */}
        {!isInputFocused && searchQuery.length === 0 && (
          <div className="absolute inset-y-0 left-4 flex items-center text-gray-400 pointer-events-none overflow-hidden">
            <span className={animationClass}>
              {PLACEHOLDER_TEXTS[placeholderIndex]}
            </span>
          </div>
        )}
        <button 
          disabled={searchQuery.length < 3 || isLoading}
          className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center bg-gray-200 text-black rounded-full hover:bg-white transition-colors duration-300 disabled:opacity-50 disabled:cursor-not-allowed">
          {isLoading ? <SpinnerIcon className="h-4 w-4" /> : <ArrowRightIcon className="h-4 w-4" />}
        </button>
      </div>

      <ContentTypeToggle activeType={activeContentType} onTypeChange={setActiveContentType} />
      
    </div>
  );
};

export default ClippingForm;
