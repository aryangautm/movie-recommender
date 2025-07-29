
import React from 'react';
import { MovieResult } from '../App';

interface TrendingCardProps {
  item: MovieResult;
}

const TrendingCard: React.FC<TrendingCardProps> = ({ item }) => {
  return (
    <div className="bg-white/5 hover:bg-white/10 rounded-xl overflow-hidden shadow-lg transition-all duration-300 transform hover:-translate-y-1 cursor-pointer">
      <img
        src={item.posterUrl.replace('128x192', '300x450')}
        alt={`${item.title} poster`}
        className="w-full h-[300px] sm:h-[250px] md:h-[250px] lg:h-[250px] aspect-[2/3] object-cover bg-gray-800"
      />
      <div className="p-4">
        <h3 className="font-bold text-white truncate text-lg">{item.title}</h3>
        <p className="text-sm text-gray-400 mt-1 line-clamp-2">{item.description}</p>
        <p className="text-xs text-gray-500 mt-2">{item.year}</p>
      </div>
    </div>
  );
};

export default TrendingCard;
