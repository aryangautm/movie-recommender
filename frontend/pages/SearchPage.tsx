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
    <div className="absolute inset-0 flex flex-col items-center justify-center p-4">
      <div className={`w-full flex flex-col items-center transition-transform duration-500 ease-in-out ${isSearchActive ? '-translate-y-16' : 'translate-y-0'}`}>
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