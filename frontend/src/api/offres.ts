import { apiClient } from './client';
import type { Offre, EnrichmentResult } from './types';

export const offresApi = {
  // Get offre by project
  getByProject: async (projectId: string): Promise<Offre> => {
    const response = await apiClient.get<Offre>(`/offres/${projectId}/offre`);
    return response.data;
  },

  // Create or update offre
  upsert: async (projectId: string, data: Offre): Promise<Offre> => {
    const response = await apiClient.post<Offre>(`/offres/${projectId}/offre`, data);
    return response.data;
  },

  // Delete offre
  delete: async (projectId: string): Promise<void> => {
    await apiClient.delete(`/offres/${projectId}/offre`);
  },

  // Enrich offre with AI
  enrich: async (projectId: string, description: string): Promise<EnrichmentResult> => {
    const response = await apiClient.post<EnrichmentResult>(`/offres/${projectId}/enrich`, {
      description,
    });
    return response.data;
  },

  // Parse offre from text
  parseText: async (projectId: string, text: string): Promise<Offre> => {
    const response = await apiClient.post<Offre>(`/offres/${projectId}/parse`, {
      text,
      model: 'gpt-5-mini',
    });
    return response.data;
  },

  // Parse offre from file (PDF/DOCX)
  parseFile: async (projectId: string, file: File): Promise<Offre> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<Offre>(`/offres/${projectId}/parse/file`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Extract criteria (must-have) via LLM
  extractCriteria: async (
    projectId: string,
    text: string
  ): Promise<{ criteria: string[]; count: number }> => {
    const response = await apiClient.post<{ criteria: string[]; count: number }>(
      `/offres/${projectId}/extract-criteria`,
      {
        text,
        model: 'gpt-5-mini',
      }
    );
    return response.data;
  },

  // Apply enrichment selections
  applyEnrichment: async (projectId: string, data: Record<string, unknown>): Promise<Offre> => {
    const response = await apiClient.post<Offre>(`/offres/${projectId}/apply`, data);
    return response.data;
  },
};
