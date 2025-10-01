import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

interface Toast {
    id: string;
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
    duration?: number;
}

interface ToastContextType {
    showToast: (message: string, type?: Toast['type'], duration?: number) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within a ToastProvider');
    }
    return context;
};

interface ToastProviderProps {
    children: React.ReactNode;
}

export const ToastProvider: React.FC<ToastProviderProps> = ({ children }) => {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const showToast = useCallback((message: string, type: Toast['type'] = 'info', duration: number = 4000) => {
        const id = Math.random().toString(36).substr(2, 9);
        const newToast: Toast = { id, message, type, duration };

        setToasts(prev => {
            const updatedToasts = [...prev, newToast];
            // Keep only the latest 4 toasts
            return updatedToasts.slice(-4);
        });

        // Auto remove toast after duration
        setTimeout(() => {
            setToasts(prev => prev.filter(toast => toast.id !== id));
        }, duration);
    }, []);

    const removeToast = useCallback((id: string) => {
        setToasts(prev => prev.filter(toast => toast.id !== id));
    }, []);

    return (
        <ToastContext.Provider value={{ showToast }}>
            {children}

            {/* Toast Container */}
            <div className="fixed bottom-20 left-1/2 transform -translate-x-1/2 z-50 space-y-2">
                {toasts.map((toast) => (
                    <ToastItem key={toast.id} toast={toast} onRemove={removeToast} />
                ))}
            </div>
        </ToastContext.Provider>
    );
};

interface ToastItemProps {
    toast: Toast;
    onRemove: (id: string) => void;
}

const ToastItem: React.FC<ToastItemProps> = ({ toast, onRemove }) => {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        // Trigger entrance animation
        setTimeout(() => setIsVisible(true), 10);
    }, []);

    const handleRemove = () => {
        setIsVisible(false);
        setTimeout(() => onRemove(toast.id), 300);
    };

    const getToastStyles = () => {
        const baseStyles = "px-4 py-3 rounded-lg shadow-lg backdrop-blur-sm border transition-all duration-300 transform w-auto min-w-64 max-w-sm mx-4";

        switch (toast.type) {
            case 'success':
                return `${baseStyles} bg-green-500/20 border-green-500/30 text-green-100`;
            case 'error':
                return `${baseStyles} bg-red-500/20 border-red-500/30 text-red-100`;
            case 'warning':
                return `${baseStyles} bg-yellow-500/20 border-yellow-500/30 text-yellow-100`;
            default:
                return `${baseStyles} bg-blue-500/20 border-blue-500/30 text-blue-100`;
        }
    };

    return (
        <div
            className={`${getToastStyles()} ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'
                }`}
        >
            <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-center flex-1">{toast.message}</p>
                <button
                    onClick={handleRemove}
                    className="ml-3 text-current opacity-70 hover:opacity-100 transition-opacity flex-shrink-0"
                    aria-label="Close toast"
                >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        </div>
    );
};
