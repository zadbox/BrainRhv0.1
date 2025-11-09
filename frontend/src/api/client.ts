import axios, { AxiosError } from 'axios';
import type { APIError } from './types';

// Base API URL (sans /api/v1 pour fichiers statiques)
export const API_BASE_URL = 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 300000, // 5 minutes (LLM calls)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour normaliser les erreurs
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<APIError>) => {
    if (error.response) {
      // Erreur du serveur (4xx, 5xx)
      const apiError: APIError = {
        code: error.response.data?.code || 'SERVER_ERROR',
        message: error.response.data?.message || 'Une erreur est survenue',
        details: error.response.data?.details,
      };
      return Promise.reject(apiError);
    } else if (error.request) {
      // Pas de réponse (réseau)
      const apiError: APIError = {
        code: 'NETWORK_ERROR',
        message: 'Impossible de contacter le serveur. Vérifiez votre connexion.',
        details: { originalError: error.message },
      };
      return Promise.reject(apiError);
    } else {
      // Erreur de configuration
      const apiError: APIError = {
        code: 'CLIENT_ERROR',
        message: error.message,
        details: {},
      };
      return Promise.reject(apiError);
    }
  }
);
