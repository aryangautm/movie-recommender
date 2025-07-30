
import React from 'react';
import { SearchIcon, TrendingIcon } from './icons';

export type NavItem = 'search' | 'trending';

const navItems: { id: NavItem; label: string; Icon: React.FC<React.SVGProps<SVGSVGElement>> }[] = [
  { id: 'search', label: 'Search', Icon: SearchIcon },
  { id: 'trending', label: 'Trending', Icon: TrendingIcon },
];

interface HeaderNavigationProps {
    activePage: NavItem;
    onNavigate: (page: NavItem) => void;
}

const HeaderNavigation: React.FC<HeaderNavigationProps> = ({ activePage, onNavigate }) => {
  return (
    <nav className="flex items-center gap-2 p-1 bg-black/30 rounded-full backdrop-blur-sm border border-white/10 shadow-lg">
      {navItems.map(({ id, label, Icon }) => (
        <button
          key={id}
          onClick={() => onNavigate(id)}
          className={`flex items-center justify-center gap-2 rounded-full transition-all duration-300 font-medium
            h-11 w-11 sm:h-auto sm:w-auto sm:py-2.5 sm:px-5
            ${
              activePage === id
                ? 'bg-gray-200 text-black shadow-md'
                : 'text-gray-300 hover:bg-white/10'
            }`}
          aria-current={activePage === id ? 'page' : undefined}
        >
          <Icon className="h-6 w-6 sm:h-5 sm:w-5" />
          <span className="hidden sm:inline text-sm">{label}</span>
        </button>
      ))}
    </nav>
  );
};

export default HeaderNavigation;
