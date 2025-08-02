
import React, { useState } from 'react';
import { Movie } from '../App';
import { UpArrowIcon, CheckIcon, SpinnerIcon } from './icons';

interface SuggestionCardProps {
  movie: Movie;
  index: number;
  onSelectMovie: (movie: Movie) => void;
  onUpvote: () => void;
}
const IMAGES_BASE_URL = 'https://image.tmdb.org/t/p';
const POSTER_SIZE = 'w300';

const SuggestionCard: React.FC<SuggestionCardProps> = ({ movie, index, onSelectMovie, onUpvote }) => {
  const posterUrl = movie.posterPath
    ? `${IMAGES_BASE_URL}/${POSTER_SIZE}${movie.posterPath}`
    : `https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=${encodeURIComponent(movie.title)}`;

  const [upvoteState, setUpvoteState] = useState<'idle' | 'loading' | 'success'>('idle');

  const handleUpvote = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (upvoteState !== 'idle') return;

    setUpvoteState('loading');
    // Simulate API call
    await new Promise(res => setTimeout(res, 1000));

    // For this example, we'll assume it always succeeds.
    setUpvoteState('success');

    // Simulate a delay before refreshing suggestions
    await new Promise(res => setTimeout(res, 500));
    onUpvote();
  };

  return (
    <div className="flex items-start gap-4">
      <span className="text-xl font-medium text-white/50 pt-3">{index}.</span>
      <div className="flex-grow bg-white/[.03] hover:bg-white/10 p-3 rounded-2xl flex items-center gap-4 transition-all duration-300 border border-white/10 cursor-pointer group" onClick={() => onSelectMovie(movie)}>
        <div className="relative flex-shrink-0">
          <div className="absolute inset-0 bg-black/20 rounded-lg -z-10"></div>
          <img
            src={posterUrl}
            alt={`${movie.title}`}
            className="w-16 h-24 object-cover rounded-lg flex-shrink-0 bg-gray-800"
          />
        </div>

        <div className="flex-grow overflow-hidden min-w-0">
          <h3 className="font-semibold text-white line-clamp-1">{movie.title}</h3>
          <p className="text-sm text-gray-400 mt-1 line-clamp-1">{movie.overview}</p>
          <p className="text-xs text-gray-500 mt-2">Year of Release: {movie.year}</p>
        </div>

        <div className="flex-shrink-0">
          <button
            onClick={handleUpvote}
            disabled={upvoteState !== 'idle'}
            className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 transform group-hover:scale-105
            ${upvoteState === 'success' ? 'bg-green-500/80 text-white' : ''}
            ${upvoteState === 'idle' ? 'bg-white/10 hover:bg-white/20 text-white/70' : ''}
            ${upvoteState === 'loading' ? 'bg-white/10 text-white/70 cursor-wait' : ''}
            `}
            aria-label={`Upvote ${movie.title}`}
          >
            {upvoteState === 'idle' && <UpArrowIcon className="w-5 h-5" />}
            {upvoteState === 'loading' && <SpinnerIcon className="w-5 h-5" />}
            {upvoteState === 'success' && <UpArrowIcon className="w-5 h-5" />}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SuggestionCard;