import { apiClient } from './client';
import type { Project, ProjectHistory } from './types';

export const projectsApi = {
  getAll: async (enterpriseId?: string): Promise<Project[]> => {
    const params = enterpriseId ? { enterprise_id: enterpriseId } : {};
    const response = await apiClient.get<Project[]>('/projects', { params });
    return response.data;
  },

  getById: async (id: string): Promise<Project> => {
    const response = await apiClient.get<Project>(`/projects/${id}`);
    return response.data;
  },

  create: async (data: Omit<Project, 'id' | 'created_at' | 'last_modified' | 'status'>): Promise<Project> => {
    const response = await apiClient.post<Project>('/projects', data);
    return response.data;
  },

  update: async (id: string, data: Partial<Omit<Project, 'id' | 'created_at' | 'last_modified'>>): Promise<Project> => {
    const response = await apiClient.put<Project>(`/projects/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/projects/${id}`);
  },

  getHistory: async (projectId: string): Promise<ProjectHistory> => {
    const response = await apiClient.get<ProjectHistory>(`/projects/${projectId}/history`);
    return response.data;
  },
};
