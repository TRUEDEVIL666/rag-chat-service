/** @type {import('tailwindcss').Config} */
export default {
    content: [
      "./index.html",
      "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: 'class',
    theme: {
      extend: {
        colors: {
          primary: {
            50: '#eff6ff',
            100: '#dbeafe',
            200: '#bfdbfe',
            300: '#93c5fd',
            400: '#60a5fa',
            500: '#3b82f6',
            600: '#2563eb', // Default Main Action Color
            700: '#1d4ed8',
            800: '#1e40af',
            900: '#1e3a8a',
            950: '#172554',
          },
          dark: {
              bg: '#111827', // gray-900
              surface: '#1f2937', // gray-800
              border: '#374151', // gray-700
          }
        },
        fontFamily: {
            sans: ['Be Vietnam Pro', 'sans-serif'],
        },
      },
    },
    plugins: [],
  }
