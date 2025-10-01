import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { SearchIcon, SpinnerIcon } from '../components/icons';
import TrendingCard from '../components/TrendingCard';
import { Movie, useHeader } from '../App';
import HeaderSearchBox from '../components/HeaderSearchBox';

import { API_URL } from '../api/config';

const formatMovieData = (item: any): Movie => ({
    id: item.id,
    title: item.title,
    year: item.release_date ? new Date(item.release_date).getFullYear() : 0,
    posterPath: item.poster_path,
    backdropPath: item.backdrop_path,
    overview: item.overview || `Overview for "${item.title}" is not available.`,
    releaseDate: String(item.release_date || 'N/A'),
    contentType: 'movie',
    runtime: 'N/A', // Not available from this endpoint
    genres: item.genres?.map((genre: any) => genre.name) || [],
    keywords: item.keywords || [],
});

const SearchFocusPage: React.FC = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const query = searchParams.get('q') || '';
    const { setCenterContent } = useHeader();

    const [movies, setMovies] = useState<Movie[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        setCenterContent(<HeaderSearchBox />);

        return () => {
            setCenterContent(null);
        };
    }, [setCenterContent]);

    useEffect(() => {
        if (!query) {
            navigate('/');
            return;
        }

        const fetchSearchResults = async () => {
            setIsLoading(true);
            setError(null);

            try {
                const response = await fetch(`${API_URL}/v1/movies/search?q=${encodeURIComponent(query)}&limit=40`);
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                const formattedResults: Movie[] = data.map(formatMovieData);

                setMovies(formattedResults);

            } catch (err) {
                console.error("Failed to fetch search results:", err);
                setError("Couldn't load search results. Please try again later.");
            } finally {
                setIsLoading(false);
            }
        };

        fetchSearchResults();
    }, [query, navigate]);

    const handleSelectMovie = (movie: Movie) => {
        navigate(`/movie/${movie.id}`);
    };

    const renderContent = () => {
        if (isLoading) {
            return (
                <div className="flex justify-center items-center py-20">
                    <SpinnerIcon className="w-12 h-12 text-white" />
                </div>
            );
        }

        if (error) {
            return <div className="text-center py-20 text-red-400 font-bold">{error}</div>;
        }

        if (movies.length === 0 && !isLoading) {
            return (
                <div className="text-center py-20 text-gray-400">
                    <p className="text-lg">No movies found for "{query}".</p>
                    <p className="text-sm mt-2">Try searching with different keywords.</p>
                </div>
            );
        }

        return (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-6">
                {movies.map(item => (
                    <TrendingCard key={item.id} item={item} onSelectMovie={handleSelectMovie} />
                ))}
            </div>
        );
    };

    return (
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex items-center gap-2 mb-4">
                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight py-2 bg-gradient-to-b from-white to-gray-400 bg-clip-text text-transparent">
                    Search Results
                </h1>
                <SearchIcon className="w-10 h-10 text-white" />
            </div>

            <div className="mb-8">
                <h2 className="text-xl sm:text-2xl text-gray-300">
                    "{query}"
                </h2>
            </div>

            {renderContent()}
        </div>
    );
};

export default SearchFocusPage;
