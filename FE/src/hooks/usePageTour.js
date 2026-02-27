import { useEffect, useRef } from 'react';
import { driver } from 'driver.js';
import 'driver.js/dist/driver.css';

/**
 * Custom hook to manage page tours using driver.js
 * @param {string} tourKey - Unique key for localStorage to track if tour was seen
 * @param {Array} steps - Array of driver.js steps
 * @returns {Object} - { startTour: () => void }
 */
export const usePageTour = (tourKey, steps) => {
  const driverObj = useRef(null);

  useEffect(() => {
    driverObj.current = driver({
      showProgress: true,
      steps: steps,
      onDestroyed: () => {
         // Optional: Do something when tour ends/is closed
      }
    });
  }, [steps]);

  const startTour = () => {
    if (driverObj.current) {
      driverObj.current.drive();
      localStorage.setItem(`tour_seen_${tourKey}`, 'true');
    }
  };

  const autoStart = () => {
      const hasSeen = localStorage.getItem(`tour_seen_${tourKey}`);
      if (!hasSeen) {
          startTour();
      }
  };

  useEffect(() => {
      // Small delay to ensure DOM is ready
      const timer = setTimeout(() => {
          autoStart();
      }, 1000); 
      return () => clearTimeout(timer);
  }, [tourKey]); // Run once per tourKey

  return { startTour };
};
