import { useState, useCallback, useRef } from 'react';
import { userService } from '../services/userService';

export const useUsers = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const nextCursorRef = useRef(null);
  const [hasMore, setHasMore] = useState(false);
  
  const [filters, setFilters] = useState({});

  const fetchUsers = useCallback(async (loadMore = false, newFilters = null) => {
    setLoading(true);
    try {
      // If new filters provided, reset cursor and use those filters
      if (newFilters) {
        nextCursorRef.current = null;
        setFilters(newFilters);
      }

      const currentFilters = newFilters || filters;
      const cursor = loadMore ? nextCursorRef.current : null;
      
      // If loading more but no cursor, stop (unless initial load which has no cursor)
      if (loadMore && !cursor) {
        setLoading(false);
        return;
      }

      const response = await userService.getUsers(20, cursor, currentFilters);
      
      const newUsers = response.items || [];
      const newNextCursor = response.next_cursor;

      setUsers(prev => {
        if (loadMore) {
          const existingIds = new Set(prev.map(u => u.id));
          const uniqueNewUsers = newUsers.filter(u => !existingIds.has(u.id));
          return [...prev, ...uniqueNewUsers];
        } 
        return newUsers; // Filter reset -> Replace list
      });
      
      nextCursorRef.current = newNextCursor;
      setHasMore(!!newNextCursor);
      setError(null);
    } catch (err) {
      setError(err);
      console.error("Failed to fetch users", err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const createUser = useCallback(async (userData) => {
    setLoading(true);
    try {
      await userService.createUser(userData);
      // Refresh list or add item
      await fetchUsers(); // Simple refresh for now
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchUsers]);

  const updateUser = useCallback(async (id, userData) => {
    setLoading(true);
    try {
      await userService.updateUser(id, userData);
      await fetchUsers();
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchUsers]);

  const deleteUser = useCallback(async (id) => {
    setLoading(true);
    try {
      await userService.deleteUser(id);
      setUsers(prev => prev.filter(u => u.id !== id));
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteUsersBatch = useCallback(async (ids) => {
    setLoading(true);
    try {
      await userService.deleteUsersBatch(ids);
      setUsers(prev => prev.filter(u => !ids.includes(u.id)));
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    users,
    loading,
    error,
    hasMore,
    fetchUsers,
    createUser,
    createUsersBatch: userService.createUsersBatch, // Exporting this too if not already
    updateUser,
    deleteUser,
    deleteUsersBatch
  };
};
