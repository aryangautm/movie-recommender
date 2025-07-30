
import React from 'react';
import { MovieResult } from '../App';
import { ArrowRightIcon } from './icons';

interface SearchResultCardProps {
  movie: MovieResult;
}

const SearchResultCard: React.FC<SearchResultCardProps> = ({ movie }) => {
  return (
    <div className="bg-white/5 hover:bg-white/10 p-3 rounded-lg flex items-center gap-4 transition-colors duration-300 cursor-pointer">
      <img
        src={movie.posterUrl}
        alt={`${movie.title} poster`}
        className="w-16 h-24 object-cover rounded-md flex-shrink-0 bg-gray-800"
      />
      <div className="flex-grow overflow-hidden">
        <h3 className="font-semibold text-white truncate">{movie.title}</h3>
        <p className="text-sm text-gray-400 mt-1 line-clamp-2">{movie.description}</p>
        <p className="text-xs text-gray-500 mt-2">{movie.year}</p>
      </div>
      <div className="flex-shrink-0">
        <ArrowRightIcon className="w-5 h-5 text-gray-500" />
      </div>
    </div>
  );
};

export default SearchResultCard;
