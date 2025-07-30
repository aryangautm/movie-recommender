
import React, { useState, useEffect } from 'react';
import { WavingHandIcon } from './components/icons';
import HeaderNavigation, { NavItem } from './components/HeaderNavigation';
import SearchPage from './pages/SearchPage';
import TrendingPage from './pages/TrendingPage';

export interface MovieResult {
  id: number;
  title: string;
  description: string;
  year: number;
  posterUrl: string;
}

const mockMovieData: MovieResult[] = [
  { id: 1, title: 'Inception', description: 'A thief who steals corporate secrets through the use of dream-sharing technology...', year: 2010, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Inception' },
  { id: 2, title: 'The Matrix', description: 'A computer hacker learns from mysterious rebels about the true nature of his reality...', year: 1999, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=The+Matrix' },
  { id: 3, title: 'Interstellar', description: 'A team of explorers travel through a wormhole in space in an attempt to ensure humanity\'s survival.', year: 2014, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Interstellar' },
  { id: 4, title: 'Parasite', description: 'Greed and class discrimination threaten the newly formed symbiotic relationship...', year: 2019, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Parasite' },
  { id: 5, title: 'The Dark Knight', description: 'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham...', year: 2008, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=The+Dark+Knight' },
];

const trendingData: MovieResult[] = [
  { id: 1, title: 'Inception', description: 'A thief who steals corporate secrets through the use of dream-sharing technology...', year: 2010, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Inception' },
  { id: 5, title: 'The Dark Knight', description: 'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham...', year: 2008, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=The+Dark+Knight' },
  { id: 2, title: 'The Matrix', description: 'A computer hacker learns from mysterious rebels about the true nature of his reality...', year: 1999, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=The+Matrix' },
  { id: 3, title: 'Interstellar', description: 'A team of explorers travel through a wormhole in space in an attempt to ensure humanity\'s survival.', year: 2014, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Interstellar' },
  { id: 4, title: 'Parasite', description: 'Greed and class discrimination threaten the newly formed symbiotic relationship...', year: 2019, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Parasite' },
  { id: 6, title: 'Pulp Fiction', description: 'The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.', year: 1994, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Pulp+Fiction' },
  { id: 7, title: 'Forrest Gump', description: 'The presidencies of Kennedy and Johnson, the Vietnam War, the Watergate scandal and other historical events unfold from the perspective of an Alabama man with an IQ of 75.', year: 1994, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Forrest+Gump' },
  { id: 8, title: 'Fight Club', description: 'An insomniac office worker looking for a way to change his life crosses paths with a devil-may-care soap maker and they form an underground fight club that evolves into something much, much more.', year: 1999, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Fight+Club' },
  { id: 9, title: 'The Lord of the Rings', description: 'A meek Hobbit from the Shire and eight companions set out on a journey to destroy the powerful One Ring and save Middle-earth from the Dark Lord Sauron.', year: 2001, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=LOTR' },
  { id: 10, title: 'Star Wars: Episode V', description: 'After the Rebels are brutally overpowered by the Empire on the ice planet Hoth, Luke Skywalker begins Jedi training with Yoda, while his friends are pursued by Darth Vader.', year: 1980, posterUrl: 'https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=Star+Wars' },
];


const App: React.FC = () => {
  const [activePage, setActivePage] = useState<NavItem>('search');
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<MovieResult[]>([]);
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
            />
          )}
          {activePage === 'trending' && (
            <TrendingPage trendingData={trendingData} />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
