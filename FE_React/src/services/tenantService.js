import api from './api';

export const getAllTenants = async () => {
  const response = await api.get('/tenants');
  return response.data;
};
