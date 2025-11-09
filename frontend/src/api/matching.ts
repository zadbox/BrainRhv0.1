import { apiClient } from './client';
import type { MatchingResponse, ResultatMatching } from './types';

export interface MatchingConfig {
  project_id: string;
  top_n_rerank?: number;
  model?: string;
}

export const matchingApi = {
  // Run matching (non-streaming)
  run: async (config: MatchingConfig): Promise<MatchingResponse> => {
    const response = await apiClient.post<MatchingResponse>('/matching/run', config);
    return response.data;
  },

  // Run matching stream (SSE)
  // Note: SSE is handled via EventSource in useSSE hook
  getRunStreamUrl: (projectId: string, topN?: number, model?: string): string => {
    const baseUrl = apiClient.defaults.baseURL || 'http://localhost:8000/api/v1';
    // Borner topN entre 1 et 10 (aligné avec config.yaml scoring.top_rerank)
    const boundedTopN = topN ? Math.min(Math.max(topN, 1), 10) : undefined;
    const params = new URLSearchParams({
      project_id: projectId,
      ...(boundedTopN && { top_n_rerank: boundedTopN.toString() }),
      ...(model && { model }),
    });
    return `${baseUrl}/matching/run/stream?${params.toString()}`;
  },

  // Get results
  getResults: async (projectId: string, timestamp: string): Promise<ResultatMatching[]> => {
    const response = await apiClient.get<{ results: ResultatMatching[] }>(
      `/matching/${projectId}/${timestamp}/results`
    );
    return response.data.results;
  },

  // Export CSV
  exportCSV: async (projectId: string, timestamp: string): Promise<Blob> => {
    const response = await apiClient.get(
      `/matching/${projectId}/${timestamp}/export/csv`,
      { responseType: 'blob' }
    );
    return response.data;
  },

  // Export Excel
  exportExcel: async (projectId: string, timestamp: string): Promise<Blob> => {
    const response = await apiClient.get(
      `/matching/${projectId}/${timestamp}/export/excel`,
      { responseType: 'blob' }
    );
    return response.data;
  },

  // Export JSON
  exportJSON: async (projectId: string, timestamp: string): Promise<Record<string, unknown>> => {
    const response = await apiClient.get<Record<string, unknown>>(
      `/matching/${projectId}/${timestamp}/export/json`
    );
    return response.data;
  },
};
