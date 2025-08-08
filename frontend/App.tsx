import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { WavingHandIcon } from './components/icons';
import HeaderNavigation from './components/HeaderNavigation';
import SearchPage from './pages/SearchPage';
import TrendingPage from './pages/TrendingPage';
import FocusPage from './pages/FocusPage';
import { Header } from '@/components/ui/Header';

export interface Movie {
  id: string;
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
  id: string;
  title: string;
  overview: string;
  releaseYear: number;
  posterPath: string;
  justification?: string[];
}

const App: React.FC = () => {
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
          <HeaderNavigation />
        </Header.Center>

        <Header.Right className="hidden sm:flex"><div /></Header.Right>
      </Header.Root>

      <div className="relative z-10 flex flex-col min-h-screen">
        <main className="relative flex-grow pt-24 sm:pt-32">
          <Routes>
            <Route path="/" element={<SearchPage />} />
            <Route path="/movies/trending" element={<TrendingPage />} />
            <Route path="/movie/:id" element={<FocusPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

export default App;