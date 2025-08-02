
import React, { useState, useEffect, useCallback } from 'react';
import ContentTypeToggle, { ContentType } from '../components/ContentTypeToggle';
import { TrendingIcon, SpinnerIcon } from '../components/icons';
import TrendingCard from '../components/TrendingCard';
import { Movie } from '../App';

interface TrendingPageProps {
    onSelectMovie: (movie: Movie) => void;
}

const BACKEND_BASE_URL = 'http://localhost:8000';

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
});

const TrendingPage: React.FC<TrendingPageProps> = ({ onSelectMovie }) => {
    const [activeType, setActiveType] = useState<ContentType>('movie');
    const [movies, setMovies] = useState<Movie[]>([]);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchTrending = useCallback(async (pageNum: number, isNewType: boolean) => {
        setIsLoading(true);
        if (isNewType) {
            setError(null);
        }

        try {
            const response = await fetch(`${BACKEND_BASE_URL}/api/v1/movies/trending?page=${pageNum}`);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            const formattedResults: Movie[] = data.results.map(formatMovieData);

            setMovies(prevMovies => isNewType ? formattedResults : [...prevMovies, ...formattedResults]);
            setPage(data.page + 1);
            setHasMore(data.page < data.total_pages);

        } catch (err) {
            console.error("Failed to fetch trending movies:", err);
            setError("Couldn't load trending movies. Please try again later.");
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        if (activeType === 'movie') {
            fetchTrending(1, true);
        } else {
            setMovies([]);
            setHasMore(false);
        }
    }, [activeType, fetchTrending]);

    useEffect(() => {
        const handleScroll = () => {
            if (window.innerHeight + document.documentElement.scrollTop < document.documentElement.offsetHeight - 500 || isLoading || !hasMore) {
                return;
            }
            if (activeType === 'movie') {
                fetchTrending(page, false);
            }
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, [isLoading, hasMore, page, activeType, fetchTrending]);

    const renderContent = () => {
        if (activeType === 'tvShow') {
            return (
                <div className="text-center py-20 text-gray-400">
                    <p className="text-lg">Trending TV shows coming soon!</p>
                </div>
            );
        }

        if (isLoading && movies.length === 0) {
            return (
                <div className="flex justify-center items-center py-20">
                    <SpinnerIcon className="w-12 h-12 text-white" />
                </div>
            )
        }

        if (error) {
            return <div className="text-center py-20 text-red-400">{error}</div>;
        }

        if (movies.length === 0 && !isLoading) {
            return (
                <div className="text-center py-20 text-gray-400">
                    <p className="text-lg">No trending movies found.</p>
                </div>
            );
        }

        return (
            <>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-6">
                    {movies.map(item => (
                        <TrendingCard key={item.id} item={item} onSelectMovie={onSelectMovie} />
                    ))}
                </div>
                {isLoading && (
                    <div className="flex justify-center items-center py-10">
                        <SpinnerIcon className="w-10 h-10 text-white" />
                    </div>
                )}
                {!isLoading && !hasMore && (
                    <div className="text-center py-10 text-gray-400">You've reached the end!</div>
                )}
            </>
        );
    }

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

            {renderContent()}
        </div>
    );
};

export default TrendingPage;