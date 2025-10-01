import React, { createContext, useState, useContext } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { HomeIcon } from './components/icons';
import HeaderNavigation from './components/HeaderNavigation';
import SearchPage from './pages/SearchPage';
import SearchFocusPage from './pages/SearchFocusPage';
import TrendingPage from './pages/TrendingPage';
import FocusPage from './pages/FocusPage';
import { Header } from '@/components/ui/Header';
import { ToastProvider } from './components/Toast';

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

interface HeaderContextType {
  centerContent: React.ReactNode;
  setCenterContent: (content: React.ReactNode) => void;
}

const HeaderContext = createContext<HeaderContextType | undefined>(undefined);

export const useHeader = () => {
  const context = useContext(HeaderContext);
  if (!context) {
    throw new Error('useHeader must be used within a HeaderProvider');
  }
  return context;
};

const App: React.FC = () => {
  const [centerContent, setCenterContent] = useState<React.ReactNode>(null);
  const navigate = useNavigate();
  const location = useLocation();

  const handleHomeClick = () => {
    navigate('/');
  };

  const isHomePage = location.pathname === '/';

  return (
    <ToastProvider>
      <HeaderContext.Provider value={{ centerContent, setCenterContent }}>
        <div data-scroll-container className="relative min-h-screen font-sans text-white bg-transparent">
          <Header.Root>
            <Header.Left className="hidden sm:flex">
              {isHomePage ? (
                <h3 className="text-xl font-bold uppercase bg-gradient-to-b from-white to-gray-300 bg-clip-text text-transparent select-none tracking-[.1em] leading-tight relative cursor-pointer group transition-all duration-300 ease-out hover:drop-shadow-[0_0_15px_rgba(255,255,255,0.4)] hover:filter hover:brightness-110">
                  <span className="relative z-10"></span>
                  <span className="absolute inset-0 text-xl font-bold uppercase text-white opacity-0 group-hover:opacity-90 transition-opacity duration-300 ease-out select-none tracking-[.1em] leading-tight">
                    MOVIESNETWORK.
                  </span>
                  <span className="absolute inset-0 text-xl font-bold uppercase text-white opacity-0 group-hover:opacity-30 transition-opacity duration-500 ease-out blur-[2px] select-none tracking-[.1em] leading-tight">
                    MOVIESNETWORK
                  </span>
                </h3>
              ) : (
                <button
                  onClick={handleHomeClick}
                  className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-black/30 rounded-full backdrop-blur-sm border border-white/10 shadow-lg hover:bg-black/40 transition-colors cursor-pointer"
                >
                  <HomeIcon className="w-4 h-4" />
                  <span>Home</span>
                </button>
              )}
            </Header.Left>

            <Header.Center>
              {centerContent || <HeaderNavigation />}
            </Header.Center>

            <Header.Right className="hidden sm:flex"><div /></Header.Right>
          </Header.Root>

          <div className="relative z-10 flex flex-col min-h-screen">
            <main className="relative flex-grow pt-24 sm:pt-32">
              <Routes>
                <Route path="/" element={<SearchPage />} />
                <Route path="/search" element={<SearchFocusPage />} />
                <Route path="/movies/trending" element={<TrendingPage />} />
                <Route path="/movie/:id" element={<FocusPage />} />
              </Routes>
            </main>
          </div>
        </div>
      </HeaderContext.Provider>
    </ToastProvider>
  );
};

export default App;