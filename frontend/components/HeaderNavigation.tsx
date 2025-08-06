
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { SearchIcon, TrendingIcon } from './icons';

export type NavItem = 'search' | 'trending';

const navItems: { id: NavItem; label: string; path: string; Icon: React.FC<React.SVGProps<SVGSVGElement>> }[] = [
  { id: 'search', label: 'Search', path: '/', Icon: SearchIcon },
  { id: 'trending', label: 'Trending', path: '/movies/trending', Icon: TrendingIcon },
];

const HeaderNavigation: React.FC = () => {
  const location = useLocation();

  return (
    <nav className="flex items-center gap-2 p-1 bg-black/30 rounded-full backdrop-blur-sm border border-white/10 shadow-lg">
      {navItems.map(({ id, label, path, Icon }) => {
        const isActive = location.pathname === path;
        return (
          <Link
            key={id}
            to={path}
            className={`flex items-center justify-center gap-2 rounded-full transition-all duration-300 font-medium
              h-11 w-11 sm:h-auto sm:w-auto sm:py-2.5 sm:px-5
              ${
                isActive
                  ? 'bg-gray-200 text-black shadow-md'
                  : 'text-gray-300 hover:bg-white/10'
              }`}
            aria-current={isActive ? 'page' : undefined}
          >
            <Icon className="h-6 w-6 sm:h-5 sm:w-5" />
            <span className="hidden sm:inline text-sm">{label}</span>
          </Link>
        );
      })}
    </nav>
  );
};

export default HeaderNavigation;
