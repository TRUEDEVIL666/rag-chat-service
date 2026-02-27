import api from './api';

export const getAllTenants = async (options = {}) => {
  const response = await api.get('/tenants', options);
  return response.data;
};
