import React, { useState, useEffect } from 'react';
import { Movie } from '../App';
import SearchResultCard from './SearchResultCard';
import { SpinnerIcon } from './icons';

interface SearchResultsProps {
  results: Movie[];
  isLoading: boolean;
  show: boolean;
  onSelectMovie: (movie: Movie) => void;
}

const SearchResults: React.FC<SearchResultsProps> = ({ results, isLoading, show, onSelectMovie }) => {
  const [shouldRender, setShouldRender] = useState(show);

  useEffect(() => {
    if (show) {
      setShouldRender(true);
    } else {
      // Wait for the exit animation to complete before removing from the DOM
      const timer = setTimeout(() => {
        setShouldRender(false);
      }, 500); // This duration should match the transition duration
      return () => clearTimeout(timer);
    }
  }, [show]);

  if (!shouldRender) {
    return null;
  }

  return (
    <div className={`w-full max-w-xl lg:max-w-2xl mt-4 transition-all duration-500 ease-in-out ${show ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
      <div className="bg-black/40 backdrop-blur-lg border border-white/10 rounded-2xl shadow-2xl p-4 max-h-[40vh] overflow-y-auto">
        {isLoading && (
          <div className="flex justify-center items-center py-10">
            <SpinnerIcon className="w-8 h-8 text-white" />
          </div>
        )}
        {!isLoading && results.length === 0 && (
          <div className="text-center py-10 text-gray-400">
            No results found. Try a different movie.
          </div>
        )}
        {!isLoading && results.length > 0 && (
          <div className="space-y-3">
            {results.map(movie => (
              <SearchResultCard key={movie.id} movie={movie} onSelectMovie={onSelectMovie} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchResults;