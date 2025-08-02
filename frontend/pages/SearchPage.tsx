import React from 'react';
import ClippingForm from '../components/ClippingForm';
import SearchResults from '../components/SearchResults';
import { Movie } from '../App';

interface SearchPageProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  isLoading: boolean;
  searchResults: Movie[];
  isSearchActive: boolean;
  onSelectMovie: (movie: Movie) => void;
}

const SearchPage: React.FC<SearchPageProps> = ({
  searchQuery,
  setSearchQuery,
  isLoading,
  searchResults,
  isSearchActive,
  onSelectMovie,
}) => {
  return (
    <div className="absolute inset-0 flex flex-col items-center p-4">
      <div
        className={`
          w-full flex flex-col items-center 
          transition-all duration-500 ease-in-out
          ${isSearchActive
            // When active, position from the top with a fixed margin and apply the desired upward translate.
            // This anchors the content, so it won't move when SearchResults' height changes.
            ? 'mt-[25vh] -translate-y-16'
            // When inactive, use this trick to vertically center the block without flexbox `justify-center`.
            // It centers the block based on its own height.
            : 'mt-[50vh] -translate-y-1/2'
          }
        `}
      >
        <div className="text-center mb-8">
          <h1 className="text-4xl sm:text-4xl lg:text-5xl font-medium bg-gradient-to-b from-white to-gray-300 bg-clip-text text-transparent pb-2">
            looking for your next watch?
          </h1>
          <p className="mt-2 text-lg text-gray-400">
            Find the feeling, not the rating.
          </p>
        </div>
        <ClippingForm
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          isLoading={isLoading}
        />
        <SearchResults
          results={searchResults}
          isLoading={isLoading}
          show={isSearchActive}
          onSelectMovie={onSelectMovie}
        />
      </div>
    </div>
  );
};

export default SearchPage;