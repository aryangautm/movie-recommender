import React from 'react';
import { Movie } from '../App';
import { ArrowRightIcon } from './icons';

interface SearchResultCardProps {
  movie: Movie;
  onSelectMovie: (movie: Movie) => void;
}

const IMAGES_BASE_URL = 'https://image.tmdb.org/t/p';
const POSTER_SIZE = 'w300';

const SearchResultCard: React.FC<SearchResultCardProps> = ({ movie, onSelectMovie }) => {
  const posterUrl = movie.posterPath
    ? `${IMAGES_BASE_URL}/${POSTER_SIZE}${movie.posterPath}`
    : `https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=${encodeURIComponent(movie.title)}`;

  return (
    <div
      className="bg-white/5 hover:bg-white/10 p-3 rounded-lg flex items-center gap-4 transition-colors duration-300 cursor-pointer"
      onClick={() => onSelectMovie(movie)}
    >
      <img
        src={posterUrl}
        alt={`${movie.title} poster`}
        className="w-16 h-24 object-cover rounded-md flex-shrink-0 bg-gray-800"
      />
      <div className="flex-grow overflow-hidden">
        <h3 className="font-semibold text-white truncate">{movie.title}</h3>
        <p className="text-sm text-gray-400 mt-1 line-clamp-2">{movie.overview}</p>
        <p className="text-xs text-gray-500 mt-2">{movie.year}</p>
      </div>
      <div className="flex-shrink-0">
        <ArrowRightIcon className="w-5 h-5 text-gray-500" />
      </div>
    </div>
  );
};

export default SearchResultCard;