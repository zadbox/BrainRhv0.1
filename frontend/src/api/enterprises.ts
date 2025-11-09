import { apiClient } from './client';
import type { Enterprise } from './types';

export const enterprisesApi = {
  getAll: async (): Promise<Enterprise[]> => {
    const response = await apiClient.get<Enterprise[]>('/enterprises');
    return response.data;
  },

  getById: async (id: string): Promise<Enterprise> => {
    const response = await apiClient.get<Enterprise>(`/enterprises/${id}`);
    return response.data;
  },

  create: async (data: Omit<Enterprise, 'id' | 'created_at' | 'last_modified' | 'projects_count'>): Promise<Enterprise> => {
    const response = await apiClient.post<Enterprise>('/enterprises', data);
    return response.data;
  },

  update: async (id: string, data: Partial<Omit<Enterprise, 'id' | 'created_at' | 'last_modified' | 'projects_count'>>): Promise<Enterprise> => {
    const response = await apiClient.put<Enterprise>(`/enterprises/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/enterprises/${id}`);
  },
};
