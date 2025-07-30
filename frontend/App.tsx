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
  releaseDate: string;
  contentType: 'movie' | 'tvShow';
  runtime: string;
  genres: string[];
}

const mockMovieData: Movie[] = [
  { id: 1, title: 'Inception', overview: 'A thief who steals corporate secrets through the use of dream-sharing technology...', year: 2010, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Inception', releaseDate: 'July 16, 2010', contentType: 'movie', runtime: '2h 28m', genres: ['Action', 'Sci-Fi', 'Thriller'] },
  { id: 2, title: 'The Matrix', overview: 'A computer hacker learns from mysterious rebels about the true nature of his reality...', year: 1999, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=The+Matrix', releaseDate: 'March 31, 1999', contentType: 'movie', runtime: '2h 16m', genres: ['Action', 'Sci-Fi'] },
  { id: 3, title: 'Interstellar', overview: "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.", year: 2014, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Interstellar', releaseDate: 'November 7, 2014', contentType: 'movie', runtime: '2h 49m', genres: ['Adventure', 'Drama', 'Sci-Fi'] },
  { id: 4, title: 'Parasite', overview: 'Greed and class discrimination threaten the newly formed symbiotic relationship...', year: 2019, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Parasite', releaseDate: 'October 11, 2019', contentType: 'movie', runtime: '2h 12m', genres: ['Comedy', 'Drama', 'Thriller'] },
  { id: 5, title: 'The Dark Knight', overview: 'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham...', year: 2008, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=The+Dark+Knight', releaseDate: 'July 18, 2008', contentType: 'movie', runtime: '2h 32m', genres: ['Action', 'Crime', 'Drama'] },
  { id: 11, title: 'Happy Gilmore 2', overview: "Happy Gilmore isn't done with golf — not by a long shot. Since his retirement after his first Tour Championship win, Gilmore returns to finance his daughter's ballet classes.", year: 2025, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Happy+Gilmore+2', releaseDate: 'July 25, 2025', contentType: 'movie', runtime: '1h 51m', genres: ['Drama', 'Fantasy'] },
  { id: 12, title: 'The Shawshank Redemption', overview: 'Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.', year: 1994, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Shawshank', releaseDate: 'September 23, 1994', contentType: 'movie', runtime: '2h 22m', genres: ['Drama'] },
  { id: 13, title: 'The Godfather', overview: 'The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.', year: 1972, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Godfather', releaseDate: 'March 24, 1972', contentType: 'movie', runtime: '2h 55m', genres: ['Crime', 'Drama'] },
  { id: 14, title: 'The Green Mile', overview: 'The lives of guards on Death Row are affected by one of their charges: a black man accused of child murder and rape, yet who has a mysterious gift.', year: 1999, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Green+Mile', releaseDate: 'December 10, 1999', contentType: 'movie', runtime: '3h 9m', genres: ['Crime', 'Drama', 'Fantasy'] },
  { id: 15, title: 'Schindler\'s List', overview: 'In German-occupied Poland during World War II, industrialist Oskar Schindler gradually becomes concerned for his Jewish workforce after witnessing their persecution by the Nazis.', year: 1993, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Schindler', releaseDate: 'February 4, 1994', contentType: 'movie', runtime: '3h 15m', genres: ['Biography', 'Drama', 'History'] },
];

const trendingData: Movie[] = [
  { id: 1, title: 'Inception', overview: 'A thief who steals corporate secrets through the use of dream-sharing technology...', year: 2010, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Inception', releaseDate: 'July 16, 2010', contentType: 'movie', runtime: '2h 28m', genres: ['Action', 'Sci-Fi', 'Thriller'] },
  { id: 5, title: 'The Dark Knight', overview: 'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham...', year: 2008, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=The+Dark+Knight', releaseDate: 'July 18, 2008', contentType: 'movie', runtime: '2h 32m', genres: ['Action', 'Crime', 'Drama'] },
  { id: 2, title: 'The Matrix', overview: 'A computer hacker learns from mysterious rebels about the true nature of his reality...', year: 1999, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=The+Matrix', releaseDate: 'March 31, 1999', contentType: 'movie', runtime: '2h 16m', genres: ['Action', 'Sci-Fi'] },
  { id: 3, title: 'Interstellar', overview: "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.", year: 2014, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Interstellar', releaseDate: 'November 7, 2014', contentType: 'movie', runtime: '2h 49m', genres: ['Adventure', 'Drama', 'Sci-Fi'] },
  { id: 4, title: 'Parasite', overview: 'Greed and class discrimination threaten the newly formed symbiotic relationship...', year: 2019, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Parasite', releaseDate: 'October 11, 2019', contentType: 'movie', runtime: '2h 12m', genres: ['Comedy', 'Drama', 'Thriller'] },
  { id: 6, title: 'Pulp Fiction', overview: 'The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.', year: 1994, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Pulp+Fiction', releaseDate: 'October 14, 1994', contentType: 'movie', runtime: '2h 34m', genres: ['Crime', 'Drama'] },
  { id: 7, title: 'Forrest Gump', overview: 'The presidencies of Kennedy and Johnson, the Vietnam War, the Watergate scandal and other historical events unfold from the perspective of an Alabama man with an IQ of 75.', year: 1994, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Forrest+Gump', releaseDate: 'July 6, 1994', contentType: 'movie', runtime: '2h 22m', genres: ['Drama', 'Romance'] },
  { id: 8, title: 'Fight Club', overview: 'An insomniac office worker looking for a way to change his life crosses paths with a devil-may-care soap maker and they form an underground fight club that evolves into something much, much more.', year: 1999, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Fight+Club', releaseDate: 'October 15, 1999', contentType: 'movie', runtime: '2h 19m', genres: ['Drama'] },
  { id: 9, title: 'The Lord of the Rings', overview: 'A meek Hobbit from the Shire and eight companions set out on a journey to destroy the powerful One Ring and save Middle-earth from the Dark Lord Sauron.', year: 2001, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=LOTR', releaseDate: 'December 19, 2001', contentType: 'movie', runtime: '2h 58m', genres: ['Action', 'Adventure', 'Drama'] },
  { id: 10, title: 'Star Wars: Episode V', overview: 'After the Rebels are brutally overpowered by the Empire on the ice planet Hoth, Luke Skywalker begins Jedi training with Yoda, while his friends are pursued by Darth Vader.', year: 1980, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Star+Wars', releaseDate: 'May 21, 1980', contentType: 'movie', runtime: '2h 4m', genres: ['Action', 'Adventure', 'Fantasy'] },
];

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
    if (debouncedQuery.length >= 3) {
      setIsLoading(true);
      setTimeout(() => {
        const filteredResults = mockMovieData.filter(movie =>
          movie.title.toLowerCase().includes(debouncedQuery.toLowerCase())
        );
        setSearchResults(filteredResults);
        setIsLoading(false);
      }, 800);
    } else {
      setSearchResults([]);
      setIsLoading(false);
    }
  }, [debouncedQuery]);

  const handleSelectMovie = (movie: Movie) => {
    setSelectedMovie(movie);
  };

  const handleGoHome = () => {
    setSelectedMovie(null);
  };

  if (selectedMovie) {
    return <FocusPage movie={selectedMovie} onGoHome={handleGoHome} onSelectMovie={handleSelectMovie} allMovies={mockMovieData} />;
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
            <TrendingPage trendingData={trendingData} onSelectMovie={handleSelectMovie} />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;