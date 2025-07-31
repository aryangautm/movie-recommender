
import React, { useState, useEffect } from 'react';
import { WavingHandIcon } from './components/icons';
import HeaderNavigation, { NavItem } from './components/HeaderNavigation';
import SearchPage from './pages/SearchPage';
import TrendingPage from './pages/TrendingPage';
import FocusPage from './pages/FocusPage';

export interface Movie {
  id: number;
  title: string;
  overview: string;
  year: number;
  posterUrl: string;
  backdropUrl?: string | null;
  releaseDate: string;
  contentType: 'movie' | 'tvShow';
  runtime: string;
  genres: string[];
}

const BACKEND_BASE_URL = 'http://localhost:8000';
const IMAGES_BASE_URL = 'https://image.tmdb.org/t/p/original';

const App: React.FC = () => {
  const [activePage, setActivePage] = useState<NavItem>('search');
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  
  // Search state
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
          posterUrl: item.poster_path
            ? `${IMAGES_BASE_URL}${item.poster_path}`
            : `https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=${encodeURIComponent(item.title)}`,
          backdropUrl: item.backdrop_path
            ? `${IMAGES_BASE_URL}${item.backdrop_path}`
            : null,
          overview: item.overview
            ? item.overview
            : `Overview for "${item.title}" is not available via search.`,
          releaseDate: String(item.release_date),
          contentType: 'movie',
          runtime: 'N/A',
          genres: item.genres.map((genre: any) => genre.name) || []
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
    setSelectedMovie(movie);
  };

  const handleGoHome = () => {
    setSelectedMovie(null);
  };

  if (selectedMovie) {
    return <FocusPage movie={selectedMovie} onGoHome={handleGoHome} onSelectMovie={handleSelectMovie} />;
  }

  return (
    <div className="relative min-h-screen font-sans text-white overflow-y-auto bg-gradient-to-b from-[#110E1B] to-[#25142d]">
      <div className="relative z-10 flex flex-col min-h-screen">
        <header className="relative flex items-center py-14 sm:p-8 md:p-8 lg:p-8">
          <div className="hidden sm:flex items-center gap-2 px-4 py-2 text-sm font-medium bg-black/30 rounded-full backdrop-blur-sm border border-white/10 shadow-lg">
            <WavingHandIcon />
            <span>Hey, Aryan!</span>
          </div>

          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
            <HeaderNavigation activePage={activePage} onNavigate={setActivePage} />
          </div>
        </header>

        <main className="flex-grow">
          {activePage === 'search' && (
            <SearchPage 
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              isLoading={isLoading}
              searchResults={searchResults}
              isSearchActive={isSearchActive}
              onSelectMovie={handleSelectMovie}
            />
          )}
          {activePage === 'trending' && (
            <TrendingPage onSelectMovie={handleSelectMovie} />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;