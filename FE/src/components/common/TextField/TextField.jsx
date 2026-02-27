import React from 'react';
import { clsx } from 'clsx';

const TextField = ({
  label,
  name,
  type = 'text',
  value,
  onChange,
  placeholder,
  required = false,
  error,
  icon: Icon,
  className,
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
          <Icon className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
        )}
        <input
          type={type}
          name={name}
          required={required}
          value={value}
          onChange={onChange}
          className={clsx(
            "w-full py-2.5 bg-white dark:bg-gray-800 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all duration-200",
            "border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400",
            Icon ? "pl-10 pr-4" : "px-4",
            error ? "border-red-500 focus:border-red-500 focus:ring-red-200" : ""
          )}
          placeholder={placeholder}
          {...props}
        />
      </div>
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  );
};

export default TextField;
