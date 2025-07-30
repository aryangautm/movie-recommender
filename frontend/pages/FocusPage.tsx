
import React from 'react';
import { Movie } from '../App';
import { LeftArrowInCircleIcon } from '../components/icons';

interface FocusPageProps {
  movie: Movie;
  onGoHome: () => void;
}

const FocusPage: React.FC<FocusPageProps> = ({ movie, onGoHome }) => {
  return (
    <div className="relative min-h-screen font-sans text-white overflow-y-auto bg-gradient-to-b from-[#110E1B] to-[#25142d]">
      {/* Back to Home Button */}
      <header className="absolute top-6 left-6 lg:top-8 lg:left-8 z-20">
        <button onClick={onGoHome} className="flex items-center gap-3 text-white/80 hover:text-white transition-colors duration-300 group">
          <LeftArrowInCircleIcon className="w-8 h-8 group-hover:scale-110 transition-transform"/>
          <span className="font-medium text-lg">Home</span>
        </button>
      </header>
      
      <main className="w-full px-4 sm:px-6 lg:px-8 pt-28 pb-12">
        <div className="w-full max-w-7xl mx-auto border border-white/10 rounded-3xl p-8 backdrop-blur-md bg-white/5 shadow-2xl">
          <div className="flex flex-col md:flex-row gap-8 lg:gap-12">
            {/* Poster */}
            <div className="w-full md:w-1/3 flex-shrink-0">
               <div className="aspect-[2/3] w-full border border-white/10 rounded-2xl flex items-center justify-center bg-black/20">
                 {/* This is a placeholder for the movie poster image, as seen in the design reference */}
               </div>
            </div>

            {/* Details */}
            <div className="w-full md:w-2/3 text-white">
              <h1 className="text-4xl lg:text-5xl font-bold">{movie.title} ({movie.year})</h1>

              <div className="flex flex-wrap items-center gap-3 mt-4">
                <span className="border border-white/20 rounded-full px-3 py-1 text-sm font-medium bg-black/20">{movie.releaseDate}</span>
                <span className="border border-white/20 rounded-full px-3 py-1 text-sm font-medium bg-black/20 capitalize">{movie.contentType}</span>
                <span className="border border-white/20 rounded-full px-3 py-1 text-sm font-medium bg-black/20">{movie.runtime}</span>
              </div>

              <div className="mt-8">
                <h2 className="text-2xl font-semibold mb-3">Genre</h2>
                <div className="flex flex-wrap gap-3">
                  {movie.genres.map(genre => (
                    <button key={genre} className="border border-white/20 rounded-full px-4 py-1.5 text-sm hover:bg-white/10 transition-colors duration-300">
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
        </div>
      </main>
    </div>
  );
};

export default FocusPage;
