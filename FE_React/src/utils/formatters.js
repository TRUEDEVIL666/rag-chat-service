/**
 * Format epoch timestamp or date string to dd/MM/yy
 * @param {number|string} epoch - Epoch timestamp in seconds or date string
 * @returns {string} Formatted date string
 */
export const formatDate = (epoch) => {
  if (!epoch) return '--';
  const date = new Date(typeof epoch === 'number' ? epoch * 1000 : epoch);
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = String(date.getFullYear()).slice(-2);
  return `${day}/${month}/${year}`;
};

/**
 * Get file extension from filename
 * @param {string} filename 
 * @returns {string} Extension (lowercase) or 'default'
 */
export const getExtension = (filename) => {
  if (!filename) return 'default';
  return filename.split('.').pop().toLowerCase();
};

/**
 * Format bytes to human readable string (B, KB, MB, GB)
 * @param {number} bytes 
 * @returns {string} Formatted size string
 */
export const formatSize = (bytes) => {
  if (!bytes) return '--';
  if (typeof bytes !== 'number') return bytes; // If already string
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`;
};
