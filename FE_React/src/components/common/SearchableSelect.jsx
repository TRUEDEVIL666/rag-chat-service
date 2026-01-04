import React, { useState, useEffect, useRef } from 'react';

const SearchableSelect = ({
  options = [],
  value,
  onChange,
  placeholder = "Select...",
  disabled = false,
  loading = false,
  allowCustom = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const wrapperRef = useRef(null);

  useEffect(() => {
    // Close dropdown when clicking outside
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [wrapperRef]);

  useEffect(() => {
    // Reset search term when dropdown closes
    if (!isOpen) {
      setSearchTerm("");
    }
  }, [isOpen]);

  const filteredOptions = options.filter(option =>
    option.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSelect = (option) => {
    onChange(option);
    setIsOpen(false);
    setSearchTerm("");
  };

  const showCustomOption = allowCustom && searchTerm && !options.some(opt => opt.toLowerCase() === searchTerm.toLowerCase());

  return (
    <div className="relative" ref={wrapperRef}>
      <div
        className={`w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 cursor-pointer flex justify-between items-center ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        onClick={() => !disabled && setIsOpen(!isOpen)}
      >
        <div className="truncate mr-2">
          <span className={!value ? "text-gray-400" : ""}>
            {value || placeholder}
          </span>
        </div>
        <div className="flex items-center flex-shrink-0">
          {loading && (
            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          )}
          <svg className={`w-4 h-4 transition-transform ${isOpen ? 'transform rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {isOpen && !disabled && (
        <div className="absolute z-50 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-lg max-h-60 overflow-auto">
          <div className="p-2 sticky top-0 bg-gray-800 border-b border-gray-700">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder={allowCustom ? "Search or type custom ID..." : "Search..."}
              className="w-full px-3 py-1 bg-gray-900 border border-gray-600 rounded text-sm text-white focus:outline-none focus:border-blue-500"
              autoFocus
              onClick={(e) => e.stopPropagation()}
            />
          </div>

          {showCustomOption && (
            <div
              className="px-4 py-2 hover:bg-gray-700 cursor-pointer text-blue-400 italic border-b border-gray-700/50"
              onClick={() => handleSelect(searchTerm)}
            >
              Use "{searchTerm}"
            </div>
          )}

          {filteredOptions.length > 0 ? (
            filteredOptions.map((option, index) => (
              <div
                key={index}
                className={`px-4 py-2 hover:bg-gray-700 cursor-pointer text-white ${value === option ? 'bg-blue-600/20 text-blue-400' : ''}`}
                onClick={() => handleSelect(option)}
              >
                {option}
              </div>
            ))
          ) : (
            !showCustomOption && <div className="px-4 py-2 text-gray-400 text-sm">No options found</div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchableSelect;
