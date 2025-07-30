import React, { useState } from 'react';
import ContentTypeToggle, { ContentType } from '../components/ContentTypeToggle';
import { TrendingIcon } from '../components/icons';
import TrendingCard from '../components/TrendingCard';
import { Movie } from '../App';

interface TrendingPageProps {
  trendingData: Movie[];
  onSelectMovie: (movie: Movie) => void;
}

const TrendingPage: React.FC<TrendingPageProps> = ({ trendingData, onSelectMovie }) => {
  const [activeType, setActiveType] = useState<ContentType>('movie');
  
  // In a real app, this would filter based on type
  const itemsToShow = trendingData;

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">        
      <div className="flex items-center gap-2 mb-8">
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight py-2 bg-gradient-to-b from-white to-gray-400 bg-clip-text text-transparent">
          Trending
        </h1>
        <TrendingIcon className="w-10 h-10 text-white" />
      </div>
      
      <div className="mb-8">
        <ContentTypeToggle activeType={activeType} onTypeChange={setActiveType} />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-6">
        {itemsToShow.map(item => (
          <TrendingCard key={item.id} item={item} onSelectMovie={onSelectMovie} />
        ))}
      </div>
    </div>
  );
};

export default TrendingPage;