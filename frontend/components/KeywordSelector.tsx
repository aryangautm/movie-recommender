import React, { useState } from 'react';

interface KeywordSelectorProps {
    keywords: string[];
    onFindSimilar: (selected: string[]) => void;
}

const KeywordSelector: React.FC<KeywordSelectorProps> = ({ keywords, onFindSimilar }) => {
    const [selectedKeywords, setSelectedKeywords] = useState<string[]>([]);

    const toggleKeyword = (keyword: string) => {
        setSelectedKeywords(prev =>
            prev.includes(keyword)
                ? prev.filter(k => k !== keyword)
                : [...prev, keyword]
        );
    };

    return (
        <div className="text-center py-4">
            <h2 className="text-2xl font-semibold mb-6 text-white/90">
                What did you like about this movie?
            </h2>
            <div className="flex flex-wrap justify-center items-center gap-3 max-w-2xl mx-auto mb-8">
                {keywords.map(keyword => (
                    <button
                        key={keyword}
                        onClick={() => toggleKeyword(keyword)}
                        className={`border rounded-full px-4 py-2 text-base font-medium transition-all duration-200 cursor-pointer
                          ${selectedKeywords.includes(keyword)
                                ? 'bg-white/90 text-[#25142d] border-transparent shadow-lg'
                                : 'bg-white/5 border-white/20 text-white/90 hover:bg-white/10 hover:border-white/30'
                            }`}
                    >
                        {keyword}
                    </button>
                ))}
            </div>
            <button
                onClick={() => onFindSimilar(selectedKeywords)}
                disabled={selectedKeywords.length === 0}
                className="text-lg font-semibold bg-white text-[#25142d] rounded-full px-10 py-3 transition-all duration-300 hover:enabled:bg-gray-200 hover:enabled:scale-105 disabled:bg-white/20 disabled:text-white/50 disabled:cursor-not-allowed"
            >
                FIND SIMILAR
            </button>
        </div>
    );
};

export default KeywordSelector;