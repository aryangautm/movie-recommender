import React from 'react';
import { Movie } from '../App';

interface TrendingCardProps {
  item: Movie;
  onSelectMovie: (movie: Movie) => void;
}

const IMAGES_BASE_URL = 'https://image.tmdb.org/t/p';
const POSTER_SIZE = 'w500';

const TrendingCard: React.FC<TrendingCardProps> = ({ item, onSelectMovie }) => {
  const posterUrl = item.posterPath
    ? `${IMAGES_BASE_URL}/${POSTER_SIZE}${item.posterPath}`
    : `https://placehold.co/128x192/1C1C1E/FFFFFF/png?text=${encodeURIComponent(item.title)}`;

  return (
    <div
      className="bg-white/5 hover:bg-white/10 rounded-xl overflow-hidden shadow-lg transition-all duration-300 transform hover:-translate-y-1 cursor-pointer"
      onClick={() => onSelectMovie(item)}
    >
      <img
        src={posterUrl}
        alt={`${item.title}`}
        className="w-full h-auto aspect-[2/3] object-cover bg-gray-800"
      />
      <div className="p-4">
        <h3 className="font-bold text-white truncate text-lg">{item.title}</h3>
        <p className="text-sm text-gray-400 mt-1 line-clamp-2">{item.overview}</p>
        <p className="text-xs text-gray-500 mt-2">{item.year}</p>
      </div>
    </div>
  );
};

export default TrendingCard;