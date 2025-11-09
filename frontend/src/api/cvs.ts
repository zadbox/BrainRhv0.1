import { apiClient } from './client';
import type { CV, CVParseResponse } from './types';

export const cvsApi = {
  // Parsing batch (non-streaming)
  parseBatch: async (files: File[]): Promise<CVParseResponse> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    const response = await apiClient.post<CVParseResponse>('/cvs/parse', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Parsing stream (SSE)
  // Note: SSE is handled via EventSource in useSSE hook
  getParseStreamUrl: (projectId?: string): string => {
    const baseUrl = apiClient.defaults.baseURL || 'http://localhost:8000/api/v1';
    return projectId
      ? `${baseUrl}/cvs/parse/stream?project_id=${projectId}`
      : `${baseUrl}/cvs/parse/stream`;
  },

  // Get all CVs from all projects
  getAll: async (): Promise<CV[]> => {
    const response = await apiClient.get<CV[]>('/cvs/all');
    return response.data;
  },

  // Get CVs by project
  getByProject: async (projectId: string): Promise<CV[]> => {
    const response = await apiClient.get<CV[]>(`/cvs/projects/${projectId}/cvs`);
    return response.data;
  },

  // Get single CV
  getById: async (cvId: string): Promise<CV> => {
    const response = await apiClient.get<CV>(`/cvs/${cvId}`);
    return response.data;
  },

  // Delete CV
  delete: async (cvId: string): Promise<void> => {
    await apiClient.delete(`/cvs/${cvId}`);
  },
};
