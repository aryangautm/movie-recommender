import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ClippingForm from '../components/ClippingForm';
import SearchResults from '../components/SearchResults';
import { Movie } from '../App';

const BACKEND_BASE_URL = 'http://localhost:8000';

const SearchPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Movie[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [debouncedQuery, setDebouncedQuery] = useState(searchQuery);

  const isSearchActive = searchQuery.length >= 3;

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 300);

    return () => {
      clearTimeout(handler);
    };
  }, [searchQuery]);

  useEffect(() => {
    if (debouncedQuery.length < 3) {
      setSearchResults([]);
      setIsLoading(false);
      return;
    }

    const fetchSearchResults = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`${BACKEND_BASE_URL}/api/v1/movies/search?q=${encodeURIComponent(debouncedQuery)}`);
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();

        const formattedResults: Movie[] = data.map((item: any) => ({
          id: item.id,
          title: item.title,
          year: item.release_date ? new Date(item.release_date).getFullYear() : 0,
          posterPath: item.poster_path,
          backdropPath: item.backdrop_path,
          overview: item.overview
            ? item.overview
            : `Overview for "${item.title}" is not available via search.`,
          releaseDate: String(item.release_date),
          contentType: 'movie',
          runtime: 'N/A',
          genres: item.genres.map((genre: any) => genre.name) || [],
          keywords: item.keywords || [],
        }));

        setSearchResults(formattedResults);
      } catch (error) {
        console.error("Failed to fetch search results:", error);
        setSearchResults([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSearchResults();
  }, [debouncedQuery]);

  const handleSelectMovie = (movie: Movie) => {
    navigate(`/movie/${movie.id}`);
  };

  return (
    <div className="absolute inset-0 flex flex-col items-center p-4">
      <div
        className={`
          w-full flex flex-col items-center 
          transition-all duration-500 ease-in-out
          ${
            isSearchActive
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
          onSelectMovie={handleSelectMovie}
        />
      </div>
    </div>
  );
};

export default SearchPage;