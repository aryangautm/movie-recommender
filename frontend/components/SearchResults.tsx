import React from 'react';
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
  const hasResults = !isLoading && results.length > 0;
  const noResults = !isLoading && results.length === 0;

  return (
    <div
      className={`
        w-full max-w-xl lg:max-w-2xl
        transition-all duration-500 ease-in-out
        ${show ? 'max-h-[40vh] opacity-100 mt-4' : 'max-h-0 opacity-0 mt-0'}
      `}
    >
      <div className="h-full rounded-2xl border border-white/10 bg-[#7D1AED]/10 p-4 shadow-2xl backdrop-blur-lg">
        {/* Grid container to stack all states and allow for smooth resizing */}
        <div className="grid">
          {/* Each state is a grid item stacked in the same cell */}
          {/* Each animates its own max-height and opacity */}

          {/* Loading State */}
          <div
            className={`
              overflow-hidden col-start-1 row-start-1
              transition-all duration-500 ease-in-out
              flex justify-center items-center
              ${isLoading ? 'max-h-40 opacity-100' : 'max-h-0 opacity-0'}
            `}
          >
            <div className="py-10">
              <SpinnerIcon className="w-8 h-8 text-white" />
            </div>
          </div>

          {/* No Results State */}
          <div
            className={`
              overflow-hidden col-start-1 row-start-1
              transition-all duration-500 ease-in-out
              text-center text-gray-400
              ${noResults ? 'max-h-40 opacity-100' : 'max-h-0 opacity-0'}
            `}
          >
            <div className="py-10">
              No results found. Try a different movie.
            </div>
          </div>

          {/* Results State */}
          <div
            className={`
              overflow-hidden col-start-1 row-start-1
              transition-all duration-500 ease-in-out
              ${hasResults ? 'max-h-[40vh] opacity-100' : 'max-h-0 opacity-0'}
            `}
          >
            <div className="space-y-3 overflow-y-auto max-h-[calc(40vh-2rem)]">
              {results.map(movie => (
                <SearchResultCard key={movie.id} movie={movie} onSelectMovie={onSelectMovie} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SearchResults;