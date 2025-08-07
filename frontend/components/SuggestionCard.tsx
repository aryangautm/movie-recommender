
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Suggestion } from '../App';
import { UpArrowIcon, SpinnerIcon } from './icons';
import { getFingerprint } from '../utils/fingerprint';

interface SuggestionCardProps {
  suggestion: Suggestion;
  index: number;
  sourceMovieId: number;
}
const IMAGES_BASE_URL = 'https://image.tmdb.org/t/p';
const POSTER_SIZE = 'w300';
const BACKEND_BASE_URL = 'http://localhost:8000';

const SuggestionCard: React.FC<SuggestionCardProps> = ({ suggestion, index, sourceMovieId }) => {
  const navigate = useNavigate();
  const posterUrl = suggestion.posterPath
    ? `${IMAGES_BASE_URL}/${POSTER_SIZE}${suggestion.posterPath}`
    : `https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=${encodeURIComponent(suggestion.title)}`;

  const [upvoteState, setUpvoteState] = useState<'idle' | 'loading' | 'success'>('idle');

  const handleUpvote = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (upvoteState !== 'idle') return;

    setUpvoteState('loading');

    try {
      const fingerprint = await getFingerprint();
      const response = await fetch(`${BACKEND_BASE_URL}/api/v1/upvote/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          movie_id_1: sourceMovieId,
          movie_id_2: suggestion.id,
          fingerprint: fingerprint,
        }),
      });

      if (!response.ok) {
        throw new Error('Upvote failed');
      }

      setUpvoteState('success');
    } catch (error) {
      console.error(error);
      setUpvoteState('idle'); // Revert to idle on failure
    }
  };

  const handleCardClick = () => {
    navigate(`/movie/${suggestion.id}`);
  };

  return (
    <div className="flex items-start gap-4 cursor-pointer" onClick={handleCardClick}>
      <span className="text-xl font-medium text-white/50 pt-3">{index}.</span>
      <div className="flex-grow bg-white/[.03] hover:bg-white/10 p-3 rounded-2xl flex items-center gap-4 transition-all duration-300 border border-white/10 group">
        <div className="relative flex-shrink-0">
          <div className="absolute inset-0 bg-black/20 rounded-lg -z-10"></div>
          <img
            src={posterUrl}
            alt={`${suggestion.title}`}
            className="w-16 h-24 object-cover rounded-lg flex-shrink-0 bg-gray-800"
          />
        </div>

        <div className="flex-grow overflow-hidden min-w-0">
          <h3 className="font-semibold text-white line-clamp-1">{suggestion.title} ({suggestion.releaseYear})</h3>
          {suggestion.justification && suggestion.justification.length > 0 ? (
            <p className="text-sm text-gray-400 mt-1 line-clamp-1">{suggestion.justification.join(', ')}</p>
          ) : (
            <p className="text-sm text-gray-400 mt-1 line-clamp-1">{suggestion.overview}</p>
          )}
          <p className="text-xs text-gray-500 mt-2">Year of Release: {suggestion.releaseYear}</p>
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
            aria-label={`Upvote ${suggestion.title}`}
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