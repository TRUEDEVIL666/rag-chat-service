import { useState, useEffect, useRef } from 'react';
import { CaretDown, Check, X, Spinner } from '@phosphor-icons/react';
import { clsx } from 'clsx';

const SearchableSelect = ({
  options = [],
  value,
  onChange,
  placeholder = "Select...",
  disabled = false,
  loading = false,
  allowCustom = false,
  className
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const wrapperRef = useRef(null);

  // Initialize search with current value's label or value
  useEffect(() => {
    if (value) {
      if (allowCustom) {
        setSearch(value);
      } else {
        const selected = options.find(o => o.value === value || o === value);
        if (selected) {
          setSearch(selected.label || selected);
        }
      }
    } else {
      setSearch('');
    }
  }, [value, options, allowCustom]);

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
        // Reset search to match selected value if not custom, or keep if custom but valid? 
        // For simplicity, just close. User sees what's in input.
        // If not custom and input doesn't match a value, reset?
        if (!allowCustom && value) {
          const selected = options.find(o => o.value === value || o === value);
          if (selected) setSearch(selected.label || selected);
          else setSearch('');
        } else if (!allowCustom && !value) {
          setSearch('');
        }
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [allowCustom, value, options]);

  const filteredOptions = options.filter(opt => {
    const label = typeof opt === 'object' ? opt.label : opt;
    const val = typeof opt === 'object' ? opt.value : opt;
    const term = search.toLowerCase();
    return String(label).toLowerCase().includes(term) || String(val).toLowerCase().includes(term);
  });

  const handleSelect = (opt) => {
    const val = typeof opt === 'object' ? opt.value : opt;
    const label = typeof opt === 'object' ? opt.label : opt;
    onChange(val);
    setSearch(label);
    setIsOpen(false);
  };

  const handleInputChange = (e) => {
    setSearch(e.target.value);
    setIsOpen(true);
    if (allowCustom) {
      onChange(e.target.value);
    }
  };

  return (
    <div className={clsx("relative", className)} ref={wrapperRef}>
      <div className="relative">
        <input
          type="text"
          value={search}
          onChange={handleInputChange}
          onClick={() => !disabled && setIsOpen(true)}
          placeholder={placeholder}
          disabled={disabled || loading}
          className={clsx(
            "w-full py-2.5 pl-4 pr-10 bg-white dark:bg-gray-800 border rounded-lg outline-none transition-all duration-200",
            "border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100",
            "focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500",
            (disabled || loading) ? "opacity-60 cursor-not-allowed" : "cursor-text"
          )}
        />

        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2 text-gray-400">
          {loading ? (
            <Spinner className="animate-spin" size={16} />
          ) : (
            <CaretDown
              size={16}
              className={clsx("transition-transform duration-200", isOpen && "rotate-180")}
              onClick={(e) => {
                e.stopPropagation();
                if (!disabled) setIsOpen(!isOpen);
              }}
            />
          )}
        </div>
      </div>

      {isOpen && !disabled && (
        <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-lg shadow-xl max-h-60 overflow-auto animate-fade-in-up">
          {filteredOptions.length === 0 ? (
            <div className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 text-center">
              {allowCustom ? 'Type to create...' : 'No options found'}
            </div>
          ) : (
            <ul className="py-1">
              {filteredOptions.map((opt, idx) => {
                const label = typeof opt === 'object' ? opt.label : opt;
                const val = typeof opt === 'object' ? opt.value : opt;
                const isSelected = val === value;

                return (
                  <li
                    key={idx}
                    onClick={() => handleSelect(opt)}
                    className={clsx(
                      "px-4 py-2 text-sm cursor-pointer flex items-center justify-between",
                      isSelected ? "bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 font-medium" : "text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700/50"
                    )}
                  >
                    <span>{label}</span>
                    {isSelected && <Check size={14} weight="bold" />}
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchableSelect;
