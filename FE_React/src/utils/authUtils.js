/**
 * Determines the home route for a user based on their role.
 * 
 * @param {Object} user - The user object containing app_metadata.
 * @returns {string} - The path to redirect the user to.
 */
export const getHomeRoute = (user) => {
  if (user?.app_metadata?.role === 'admin') {
    return '/admin';
  }
  return '/user';
};
