import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { SearchIcon } from './icons';
import SearchResults from './SearchResults';
import { Movie } from '../App';
import { API_URL } from '../api/config';

interface HeaderSearchBoxProps {
    placeholder?: string;
    placeholderWords?: string[];
    onSearch?: (query: string) => void;
}

// Custom hook for typing animation
const useTypingAnimation = (words: string[], typingSpeed = 100, deletingSpeed = 50, pauseDuration = 2000) => {
    const [currentText, setCurrentText] = useState('');
    const [currentWordIndex, setCurrentWordIndex] = useState(0);
    const [isDeleting, setIsDeleting] = useState(false);
    const [showCursor, setShowCursor] = useState(true);

    useEffect(() => {
        // Cursor blinking effect
        const cursorInterval = setInterval(() => {
            setShowCursor(prev => !prev);
        }, 530);

        return () => clearInterval(cursorInterval);
    }, []);

    useEffect(() => {
        if (words.length === 0) return;

        const currentWord = words[currentWordIndex];

        const timeout = setTimeout(() => {
            if (!isDeleting) {
                // Typing
                if (currentText.length < currentWord.length) {
                    setCurrentText(currentWord.slice(0, currentText.length + 1));
                } else {
                    // Finished typing, wait then start deleting
                    setTimeout(() => setIsDeleting(true), pauseDuration);
                }
            } else {
                // Deleting
                if (currentText.length > 0) {
                    setCurrentText(currentText.slice(0, -1));
                } else {
                    // Finished deleting, move to next word
                    setIsDeleting(false);
                    setCurrentWordIndex((prev) => (prev + 1) % words.length);
                }
            }
        }, isDeleting ? deletingSpeed : typingSpeed);

        return () => clearTimeout(timeout);
    }, [currentText, currentWordIndex, isDeleting, words, typingSpeed, deletingSpeed, pauseDuration]);

    return `${currentText}${showCursor ? '|' : ' '}`;
};

const HeaderSearchBox: React.FC<HeaderSearchBoxProps> = ({
    placeholder = "|",
    placeholderWords = [
        "Sholay",
        "Citizen Kane",
        "3 Idiots",
        "Casablanca",
        "Mughal-E-Azam",
        "The Dark Knight",
        "Tumbbad",
        "Pulp Fiction",
        "Lagaan",
        "Forrest Gump",
        "The Godfather",
        "Mother India",
        "Inception",
        "Schindler's List",
        "Andaz Apna Apna",
        "Fight Club",
        "Gully Boy",
        "The Matrix",
        "Chak De! India",
        "Goodfellas",
        "Queen",
        "The Lion King",
        "Barfi!",
        "Interstellar",
        "The Prestige",
        "Swades",
        "Parasite",
        "Taare Zameen Par",
        "The Lord of the Rings",
        "Joker",
        "Drishyam",
        "The Social Network",
        "Dangal",
        "Gangs of Wasseypur",
        "Haider",
        "Barfi!",
        "Mad Max: Fury Road",
        "Queen",
        "The Lunchbox",
        "Whiplash"
    ],
    onSearch
}) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<Movie[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [debouncedQuery, setDebouncedQuery] = useState(searchQuery);
    const [showResults, setShowResults] = useState(true);
    const [isExpanded, setIsExpanded] = useState(false);
    const [isFocused, setIsFocused] = useState(false);
    const navigate = useNavigate();
    const searchContainerRef = useRef<HTMLDivElement>(null);

    const isSearchActive = searchQuery.length >= 2 && showResults && isFocused;

    // Use typing animation if placeholderWords are provided, otherwise use static placeholder
    const animatedPlaceholder = useTypingAnimation(placeholderWords);
    const displayPlaceholder = placeholderWords.length > 0 ? animatedPlaceholder : placeholder;

    // Debouncing effect
    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedQuery(searchQuery);
        }, 300);

        return () => {
            clearTimeout(handler);
        };
    }, [searchQuery]);

    // Click outside detection
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
                setShowResults(false);
                setIsExpanded(false);
                setIsFocused(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    // Reset showResults when search query changes, but only if focused
    useEffect(() => {
        if (searchQuery.length >= 2 && isFocused) {
            setShowResults(true);
        } else if (searchQuery.length < 2) {
            setShowResults(false);
        }
    }, [searchQuery, isFocused]);

    // Update expansion state based on focus
    useEffect(() => {
        setIsExpanded(isFocused);
    }, [isFocused]);

    // Search effect
    useEffect(() => {
        if (debouncedQuery.length < 2) {
            setSearchResults([]);
            setIsLoading(false);
            return;
        }

        const fetchSearchResults = async () => {
            setIsLoading(true);
            try {
                const response = await fetch(`${API_URL}/v1/movies/search?q=${encodeURIComponent(debouncedQuery)}`);
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();

                const formattedResults: Movie[] = data.map((item: any) => ({
                    id: item.id,
                    title: item.title,
                    year: item.release_date ? new Date(item.release_date).getFullYear() : 0,
                    posterPath: item.poster_path,
                    backdropPath: item.backdrop_path,
                    overview: item.overview
                        ? item.overview
                        : `Overview for "${item.title}" is not available via search.`,
                    releaseDate: String(item.release_date),
                    contentType: 'movie',
                    runtime: 'N/A',
                    genres: item.genres.map((genre: any) => genre.name) || [],
                    keywords: item.keywords || [],
                }));

                setSearchResults(formattedResults);
            } catch (error) {
                console.error("Failed to fetch search results:", error);
                setSearchResults([]);
            } finally {
                setIsLoading(false);
            }
        };

        fetchSearchResults();
    }, [debouncedQuery]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (searchQuery.trim()) {
            if (onSearch) {
                onSearch(searchQuery.trim());
            } else {
                // Default behavior: navigate to search focus page with query
                navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
            }
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchQuery(e.target.value);
    };

    const handleInputFocus = () => {
        setIsFocused(true);
        // Show results if we have a valid search query
        if (searchQuery.length >= 2) {
            setShowResults(true);
        }
    };

    const handleInputBlur = () => {
        // Add a small delay to allow for result selection
        setTimeout(() => {
            if (!searchContainerRef.current?.contains(document.activeElement)) {
                setIsFocused(false);
                setShowResults(false);
            }
        }, 150);
    };

    const handleSelectMovie = (movie: Movie) => {
        setShowResults(false);
        setIsFocused(false);
        navigate(`/movie/${movie.id}`);
    };

    const handleSearchIconClick = () => {
        if (searchQuery.trim().length >= 3) {
            navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
        }
    };

    return (
        <div className="relative" ref={searchContainerRef}>
            <form
                onSubmit={handleSubmit}
                className={`flex items-center gap-4 p-1 bg-black/30 rounded-full backdrop-blur-sm border border-white/10 shadow-lg transition-all duration-500 ease-out ${isExpanded
                    ? 'w-[calc(100vw-2rem)] sm:w-[20rem] md:w-[22rem] lg:w-[25rem]'
                    : 'w-[12rem] sm:w-[14rem] md:w-[15rem]'
                    } ${isExpanded ? 'animate-bounce-subtle' : ''}`}
                style={{
                    animationDuration: isExpanded ? '0.6s' : '0s',
                    animationFillMode: 'forwards'
                }}
            >
                <div
                    onClick={handleSearchIconClick}
                    className={`flex items-center justify-center gap-2 rounded-full transition-all duration-300 font-medium h-11 w-11 sm:h-auto sm:w-auto sm:py-2.5 sm:px-5 bg-gray-200 text-black shadow-md ${searchQuery.trim().length >= 3
                        ? 'cursor-pointer hover:bg-white hover:scale-105'
                        : 'cursor-default opacity-100'
                        }`}
                >
                    <SearchIcon className="h-6 w-6 sm:h-5 sm:w-5" />
                </div>
                <input
                    type="text"
                    value={searchQuery}
                    onChange={handleInputChange}
                    onFocus={handleInputFocus}
                    onBlur={handleInputBlur}
                    placeholder={displayPlaceholder}
                    className="bg-transparent text-white placeholder-gray-400/50 outline-none text-sm font-medium pr-4 py-2.5 min-w-0 flex-1"
                />
            </form>
            <div className="absolute top-full left-0 right-0 z-50 mt-2">
                <SearchResults
                    results={searchResults}
                    isLoading={isLoading}
                    show={isSearchActive}
                    onSelectMovie={handleSelectMovie}
                    backgroundColor="bg-black/70"
                />
            </div>
        </div>
    );
};

export default HeaderSearchBox;
