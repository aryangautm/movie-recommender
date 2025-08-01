import React from 'react';
import { clsx } from 'clsx';

interface HeaderRootProps extends React.HTMLAttributes<HTMLElement> {
    children: React.ReactNode;
    isScrolled?: boolean;
}

interface HeaderSectionProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode;
}


const Root: React.FC<HeaderRootProps> = ({
    children,
    isScrolled = false,
    className,
    ...props
}) => {
    return (
        <header
            className={clsx(
                'fixed top-0 left-0 right-0 z-40 grid grid-cols-3 items-center gap-4 py-4 px-4 sm:px-8 transition-all duration-300',
                {
                    'bg-gradient-to-b from-black/90 via-black/40 to-transparent':
                        isScrolled,
                    'bg-transparent': !isScrolled,
                },
                className
            )}
            {...props}
        >
            {children}
        </header>
    );
};

const Left: React.FC<HeaderSectionProps> = ({ children, className, ...props }) => {
    return (
        <div className={clsx('justify-self-start', className)} {...props}>
            {children}
        </div>
    );
};

const Center: React.FC<HeaderSectionProps> = ({
    children,
    className,
    ...props
}) => {
    return (
        <div
            className={clsx('justify-self-center col-start-2', className)}
            {...props}
        >
            {children}
        </div>
    );
};

const Right: React.FC<HeaderSectionProps> = ({
    children,
    className,
    ...props
}) => {
    return (
        <div className={clsx('justify-self-end', className)} {...props}>
            {children}
        </div>
    );
};


export const Header = {
    Root,
    Left,
    Center,
    Right,
};