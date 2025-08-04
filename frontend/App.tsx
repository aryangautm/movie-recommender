import React, { useState, useEffect } from 'react';
import { WavingHandIcon } from './components/icons';
import HeaderNavigation, { NavItem } from './components/HeaderNavigation';
import SearchPage from './pages/SearchPage';
import TrendingPage from './pages/TrendingPage';
import FocusPage from './pages/FocusPage';
import { Header } from '@/components/ui/Header';
// import Stars from './components/Stars';

export interface Movie {
  id: number;
  title: string;
  overview: string;
  year: number;
  posterPath: string;
  backdropPath?: string | null;
  releaseDate: string;
  contentType: 'movie' | 'tvShow';
  runtime: string;
  genres: string[];
  keywords?: string[];
}
export interface Suggestion {
  id: number;
  title: string;
  overview: string;
  releaseYear: number;
  posterPath: string;
  justification?: string[];
}


const BACKEND_BASE_URL = 'http://localhost:8000';
const IMAGES_BASE_URL = 'https://image.tmdb.org/t/p';
const POSTER_SIZE = 'w500';
const BACKDROP_SIZE = 'w780';

const App: React.FC = () => {
  const [activePage, setActivePage] = useState<NavItem>('search');
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Movie[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [debouncedQuery, setDebouncedQuery] = useState(searchQuery);

  const isSearchActive = searchQuery.length >= 3;
  // const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  // useEffect(() => {
  //   const handleMouseMove = (event: MouseEvent) => {
  //     setMousePos({ x: event.clientX, y: event.clientY });
  //   };

  //   window.addEventListener('mousemove', handleMouseMove);

  //   // Cleanup function to remove the listener when the component unmounts
  //   return () => {
  //     window.removeEventListener('mousemove', handleMouseMove);
  //   };
  // }, []);

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
    setSelectedMovie(movie);
  };

  const handleGoHome = () => {
    setSelectedMovie(null);
  };

  if (selectedMovie) {
    return <FocusPage movie={selectedMovie} onGoHome={handleGoHome} onSelectMovie={handleSelectMovie} />;
  }

  return (
    <div data-scroll-container className="relative min-h-screen font-sans text-white bg-transparent">
      <Header.Root>
        <Header.Left className="hidden sm:flex">
          <div className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-black/30 rounded-full backdrop-blur-sm border border-white/10 shadow-lg">
            <WavingHandIcon />
            <span>Hey!</span>
          </div>
        </Header.Left>

        <Header.Center>
          <HeaderNavigation activePage={activePage} onNavigate={setActivePage} />
        </Header.Center>

        <Header.Right className="hidden sm:flex"><div /></Header.Right>
      </Header.Root>

      <div className="relative z-10 flex flex-col min-h-screen">
        <main className="relative flex-grow pt-24 sm:pt-32">
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