import React from 'react';
import { clsx } from 'clsx';
import { CaretDown } from '@phosphor-icons/react';

const Select = ({
  label,
  name,
  value,
  onChange,
  options = [],
  placeholder = "Select an option",
  required = false,
  error,
  icon: Icon,
  className,
  loading = false,
  disabled = false,
  ...props
}) => {
  return (
    <div className={clsx("space-y-2", className)}>
      {label && (
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {label} {required && <span className="text-red-500">*</span>}
        </label>
      )}
      <div className="relative">
        {Icon && (
          <Icon className="absolute left-3 top-1/2 -translate-y-1/2 z-10 text-gray-400" size={20} />
        )}

        <select
          name={name}
          required={required}
          value={value}
          onChange={onChange}
          disabled={disabled || loading}
          className={clsx(
            "w-full py-2.5 bg-white dark:bg-gray-800 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all duration-200 appearance-none cursor-pointer",
            "border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100",
            Icon ? "pl-10 pr-10" : "px-4 pr-10",
            error ? "border-red-500" : "",
            (disabled || loading) ? "opacity-60 cursor-not-allowed" : ""
          )}
          {...props}
        >
          <option value="" disabled>{loading ? "Loading..." : placeholder}</option>
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
          <CaretDown size={16} />
        </div>
      </div>
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  );
};

export default Select;
