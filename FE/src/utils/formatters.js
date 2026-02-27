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
 * Format bytes to human readable string (B, KB, MB, GB, etc.)
 * @param {number} bytes 
 * @param {number} decimals 
 * @returns {string} Formatted size string
 */
export const formatBytes = (bytes, decimals = 2) => {
  if (bytes === 0 || !bytes) return '0 B';
  if (typeof bytes !== 'number') return bytes; // If already string

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};
