import React from 'react';
import ClippingForm from '../components/ClippingForm';
import SearchResults from '../components/SearchResults';
import { MovieResult } from '../App';

interface SearchPageProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  isLoading: boolean;
  searchResults: MovieResult[];
  isSearchActive: boolean;
}

const SearchPage: React.FC<SearchPageProps> = ({
  searchQuery,
  setSearchQuery,
  isLoading,
  searchResults,
  isSearchActive,
}) => {
  return (
    <div className="flex flex-col items-center justify-center flex-grow p-4">
      <div className={`w-full flex flex-col items-center transition-transform duration-500 ease-in-out ${isSearchActive ? 'translate-y-24' : 'translate-y-[10rem] sm:translate-y-56 md:translate-y-56 lg:translate-y-56'}`}>
        <div className="text-center mb-8">
          <h1 className="text-4xl sm:text-4xl lg:text-5xl font-medium bg-gradient-to-b from-white to-gray-400 bg-clip-text text-transparent pb-2">
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
        />
      </div>
    </div>
  );
};

export default SearchPage;
