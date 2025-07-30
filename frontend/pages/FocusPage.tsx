import React, { useState, useEffect, useCallback } from 'react';
import { Movie } from '../App';
import { LeftArrowInCircleIcon } from '../components/icons';
import SuggestionCard from '../components/SuggestionCard';

interface FocusPageProps {
  movie: Movie;
  onGoHome: () => void;
  onSelectMovie: (movie: Movie) => void;
  allMovies: Movie[];
}


const FocusPage: React.FC<FocusPageProps> = ({ movie, onGoHome, onSelectMovie, allMovies }) => {
  const [suggestions, setSuggestions] = useState<Movie[]>([]);

  const fetchSuggestions = useCallback(() => {
    const similar = allMovies
      .filter(m => m.id !== movie.id)
      .sort(() => 0.5 - Math.random())
      .slice(0, 4);
    setSuggestions(similar);
  }, [movie.id, allMovies]);

  useEffect(() => {
    fetchSuggestions();
    window.scrollTo(0, 0);
  }, [movie.id, fetchSuggestions]);

  const SuggestionsContent = (
    <>
      <h2 className="text-2xl font-semibold mb-6">Similar Suggestions</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-8">
        {suggestions.map((suggestion, index) => (
          <SuggestionCard
            key={suggestion.id}
            movie={suggestion}
            index={index + 1}
            onSelectMovie={onSelectMovie}
            onUpvote={fetchSuggestions}
          />
        ))}
      </div>
    </>
  );

  return (
    <div className="relative min-h-screen font-sans text-white overflow-y-auto bg-gradient-to-b from-[#110E1B] to-[#25142d]">
      {/* Back to Home Button */}
      <header className="absolute top-6 left-6 lg:top-8 lg:left-8 z-20">
        <button onClick={onGoHome} className="flex items-center gap-3 text-white/80 hover:text-white transition-colors duration-300 group">
          <LeftArrowInCircleIcon className="w-8 h-8 group-hover:scale-110 transition-transform" />
          <span className="font-medium text-lg">Home</span>
        </button>
      </header>

      <main className="w-full px-4 sm:px-6 lg:px-8 pt-28 pb-12">
        <div className="relative w-full max-w-7xl mx-auto border border-white/10 rounded-3xl shadow-2xl overflow-hidden bg-black/30">
          
          {/* 1. Backdrop image at z‑0 */}
          {movie.backdropUrl && (
            <div
              className="absolute inset-0 w-full h-full bg-cover bg-center opacity-25 z-0"
              style={{ backgroundImage: `url(${movie.backdropUrl})` }}
            />
          )}

          {/* 2. Gradient overlay at z‑10 */}
          <div
            className="absolute inset-0 bg-gradient-to-b from-black/20 via-[#110E1B]/50 to-[#110E1B] z-10"
          />

          {/* 3. Content at z‑20 */}
          <div className="relative z-20 p-6 sm:p-8">
            <div className="flex flex-col sm:flex-row md:flex-row gap-8 lg:gap-12">
              {/* Poster */}
              <div className="w-1/2 sm:w-1/3 flex-shrink-0 mx-auto md:mx-0">
                <div className="aspect-[2/3] w-full border border-white/10 rounded-2xl flex items-center justify-center bg-black/20 shadow-lg">
                  <img
                    src={movie.posterUrl.replace('128x192', '300x450')}
                    alt={`${movie.title}`}
                    className="w-full h-full object-cover rounded-2xl"
                  />
                </div>
              </div>

              {/* Details */}
              <div className="w-full md:w-2/3">
                <h1 className="text-4xl lg:text-5xl font-bold">
                  {movie.title} ({movie.year})
                </h1>

                <div className="flex flex-wrap items-center gap-3 mt-4">
                  <span className="border border-white/20 rounded-full px-3 py-1 text-sm font-medium bg-black/20">
                    {movie.releaseDate}
                  </span>
                  <span className="border border-white/20 rounded-full px-3 py-1 text-sm font-medium bg-black/20 capitalize">
                    {movie.contentType}
                  </span>
                </div>

                <div className="mt-8">
                  <h2 className="text-2xl font-semibold mb-3">Genre</h2>
                  <div className="flex flex-wrap gap-3">
                    {movie.genres.map(genre => (
                      <button
                        key={genre}
                        className="border border-white/20 rounded-full px-4 py-1.5 text-sm hover:bg-white/10 transition-colors duration-300"
                      >
                        {genre}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="mt-8">
                  <h2 className="text-2xl font-semibold mb-3">Overview</h2>
                  <p className="text-white/80 leading-relaxed text-base">
                    {movie.overview}
                  </p>
                </div>
              </div>
            </div>

            {/* Suggestions for MD and up */}
            <div className="block mt-8 pt-8 border-t border-white/10">
              {SuggestionsContent}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default FocusPage;
