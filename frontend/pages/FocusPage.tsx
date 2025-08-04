import React, { useState, useEffect, useCallback } from 'react';
import { Movie, Suggestion } from '@/App';
import { LeftArrowInCircleIcon, SpinnerIcon } from '@/components/icons';
import SuggestionCard from '@/components/SuggestionCard';
import { Header } from '@/components/ui/Header';
import KeywordSelector from '@/components/KeywordSelector';

interface FocusPageProps {
  movie: Movie;
  onGoHome: () => void;
  onSelectMovie: (movie: Movie) => void;
}

const BACKEND_BASE_URL = 'http://localhost:8000';
const IMAGES_BASE_URL = 'https://image.tmdb.org/t/p';
const POSTER_SIZE = 'original';
const BACKDROP_SIZE = 'original';

const FocusPage: React.FC<FocusPageProps> = ({ movie, onGoHome, onSelectMovie }) => {
  const posterUrl = movie.posterPath
    ? `${IMAGES_BASE_URL}/${POSTER_SIZE}${movie.posterPath}`
    : `https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=${encodeURIComponent(movie.title)}`;

  const backdropUrl = movie.backdropPath
    ? `${IMAGES_BASE_URL}/${BACKDROP_SIZE}${movie.backdropPath}`
    : null;

  type SuggestionState = 'selecting' | 'loading' | 'showing';

  const [suggestionState, setSuggestionState] = useState<SuggestionState>('selecting');
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSuggestions = useCallback(async (options?: { keywords?: string[]; isRefresh?: boolean }) => {
    if (options?.isRefresh) {
      console.log('Refreshing suggestions...');
    } else {
      console.log('Fetching suggestions...');
    }

    setIsLoadingSuggestions(true);
    setSuggestionState('loading'); // Transition to loading view to show spinner
    setError(null);

    try {
      let data;
      let response;
      let keywords = options?.keywords || [];

      // POST request for keyword-based recommendations
      console.log('Finding recommendations based on keywords:', keywords);
      response = await fetch(`${BACKEND_BASE_URL}/api/v1/recommendations/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          source_movie_id: movie.id,
          selected_keywords: keywords,
        }),
      });
      if (!response.ok) { throw new Error('Network response for recommendations was not ok'); }
      const result = await response.json();
      data = result.results;

      const formattedSuggestions: Suggestion[] = data.map((item: any) => ({
        id: item.id,
        title: item.title,
        releaseYear: item.release_year,
        posterPath: item.poster_path,
        overview: item.overview || `Overview for "${item.title}" is not available.`,
        justification: item.justification || [],
      }));

      setSuggestions(formattedSuggestions);
      setSuggestionState('showing');
    } catch (err: any) {
      console.error("Failed to fetch suggestions:", err);
      setError(err.message || "Couldn't load suggestions. Please try again later.");
      setSuggestions([]);
      setSuggestionState('showing'); // Transition to show the error message
    } finally {
      setIsLoadingSuggestions(false);
    }
  }, [movie.id]);

  // This effect now correctly handles the initial state when the movie changes.
  useEffect(() => {
    window.scrollTo(0, 0);
    setSuggestions([]);
    setError(null);

    const hasKeywords = movie.keywords && movie.keywords.length > 0;
    if (hasKeywords) {
      // If there are keywords, start in the 'selecting' state.
      setSuggestionState('selecting');
      setIsLoadingSuggestions(false);
    } else {
      // If no keywords, fetch default suggestions immediately.
      fetchSuggestions();
    }
  }, [movie.id, movie.keywords, fetchSuggestions]);


  const handleFindSimilar = (selectedKeywords: string[]) => {
    // This action now directly calls the fetch logic.
    fetchSuggestions({ keywords: selectedKeywords });
  };

  const handleRefreshSuggestions = useCallback(() => {
    // Re-fetch default suggestions
    fetchSuggestions({ isRefresh: true });
  }, [fetchSuggestions]);


  const SuggestionsContent = (
    <>
      <h2 className="text-2xl font-semibold mb-6">Similar Suggestions</h2>
      {isLoadingSuggestions ? (
        <div className="flex justify-center items-center py-10">
          <SpinnerIcon className="w-8 h-8 text-white" />
        </div>
      ) : error ? (
        <div className="text-center py-10 text-red-400">{error}</div>
      ) : suggestions.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-8">
          {suggestions.map((suggestion, index) => (
            <SuggestionCard
              key={suggestion.id}
              suggestion={suggestion}
              index={index + 1}
              onUpvote={handleRefreshSuggestions}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-10 text-gray-400">
          No similar suggestions found.
        </div>
      )}
    </>
  );

  return (
    <div className="relative h-screen font-sans text-white overflow-hidden">
      {/* Back to Home Button */}
      <Header.Root>
        <Header.Left className="hidden sm:flex">
          <button onClick={onGoHome} className="flex items-center gap-3 text-white/80 hover:text-white transition-colors duration-300 group">
            <LeftArrowInCircleIcon className="w-8 h-8 group-hover:scale-110 transition-transform" />
            <span className="font-medium text-lg">Home</span>
          </button>
        </Header.Left>
      </Header.Root>

      <main className="w-full h-full px-4 sm:px-6 lg:px-8 pt-28 pb-12 overflow-y-auto">
        <div className="max-w-7xl mx-auto">
          {/* Main Content Container */}
          <div className="w-full border border-white/10 rounded-3xl shadow-2xl overflow-hidden bg-black/30">

            {/* Movie Details Section with Backdrop */}
            <div className="relative overflow-hidden">
              {/* 1. Backdrop image at z‑0 */}
              {backdropUrl && (
                <div
                  className="absolute inset-0 w-full h-full bg-cover bg-center z-0"
                  style={{ backgroundImage: `url(${backdropUrl})` }}
                />
              )}

              {/* 2. Gradient overlay at z‑10 */}
              <div
                className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/70 to-black/100 z-10"
              />

              {/* 3. Content at z‑20 */}
              <div className="relative z-20 p-6 sm:p-8">
                <div className="flex flex-col sm:flex-row md:flex-row gap-8 lg:gap-12">
                  {/* Poster */}
                  <div className="w-1/2 sm:w-1/3 flex-shrink-0 mx-auto md:mx-0">
                    <div className="aspect-[2/3] w-full border border-white/10 rounded-2xl flex items-center justify-center bg-black/20 shadow-lg">
                      <img
                        src={posterUrl}
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
                      <p className="text-white leading-relaxed text-base">
                        {movie.overview}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Suggestions Section */}
            <div className="p-6 sm:p-8 bg-[#7D1AED]/10">
              {suggestionState === 'selecting' && movie.keywords && movie.keywords.length > 0 ? (
                <KeywordSelector keywords={movie.keywords} onFindSimilar={handleFindSimilar} />
              ) : (
                SuggestionsContent
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default FocusPage;