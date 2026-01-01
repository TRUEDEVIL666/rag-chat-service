const config = {
  api: {
    baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1',
    timeout: 60000, // 60 seconds
  },
  app: {
    name: 'RAG Chat Service',
    version: '1.0.0',
  }
};

export default config;
