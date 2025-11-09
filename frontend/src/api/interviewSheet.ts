import { apiClient } from './client';

export interface InterviewSheet {
  id: string;
  candidate_id: string;
  job_id: string;
  matching_id: string;
  interviewer_id: string;
  status: 'draft' | 'in_progress' | 'completed';
  data: InterviewSheetData;
  json_path: string;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  pdf_url: string | null;
}

export interface InterviewQuestionItem {
  theme?: string;
  items?: string[];
  question?: string;
  criteria?: string;
  notes?: string;
  score?: number;
  asked?: boolean;
  satisfactory?: boolean;
}

export interface InterviewScorecardItem {
  criterion: string;
  weight: number;
  description: string;
  score?: number;
  justification?: string;
  [key: string]: unknown;
}

export interface InterviewSheetData {
  resume?: string;
  strengths?: Array<{ point: string; evidence: string }>;
  concerns?: Array<{ point: string; question: string }>;
  questions?: InterviewQuestionItem[];
  evaluation_grid?: InterviewScorecardItem[];
  // Champs additionnels éditables
  scorecard?: InterviewScorecardItem[];
  free_notes?: string;
  recommendation?: string;
  verdict?: string;
  verdict_detail?: string;
  additional_tests?: boolean;
  residual_risks?: string;
}

export interface UpdateInterviewSheetInput {
  scorecard?: InterviewScorecardItem[];
  questions?: InterviewQuestionItem[];
  free_notes?: string;
  recommendation?: string;
  status?: 'draft' | 'in_progress';
  verdict?: string;
  verdict_detail?: string;
  additional_tests?: boolean;
  residual_risks?: string;
}

export interface GenerateInterviewSheetInput {
  candidate_id: string;
  job_id: string;
  matching_id: string;
  interviewer_id: string;
}

export interface GenerateInterviewSheetResponse {
  interview_sheet_id: string;
  status: string;
  data: InterviewSheetData;
  existing: boolean;
}

export interface ListInterviewSheetsParams {
  job_id?: string;
  limit?: number;
}

export interface ListInterviewSheetsResponse {
  sheets: InterviewSheet[];
  total: number;
}

export const interviewSheetApi = {
  // List all interview sheets with optional filters
  listAll: async (params?: ListInterviewSheetsParams): Promise<ListInterviewSheetsResponse> => {
    const response = await apiClient.get<ListInterviewSheetsResponse>('/interview-sheet/', { params });
    return response.data;
  },

  // Generate or open existing interview sheet
  generateOrOpen: async (input: GenerateInterviewSheetInput): Promise<GenerateInterviewSheetResponse> => {
    const response = await apiClient.post<GenerateInterviewSheetResponse>('/interview-sheet/generate', input);
    return response.data;
  },

  // Get interview sheet by ID
  getById: async (sheetId: string): Promise<InterviewSheet> => {
    const response = await apiClient.get<InterviewSheet>(`/interview-sheet/${sheetId}`);
    return response.data;
  },

  // Update interview sheet
  patch: async (sheetId: string, data: UpdateInterviewSheetInput): Promise<{ success: boolean; updated_at: string }> => {
    const response = await apiClient.patch<{ success: boolean; updated_at: string }>(
      `/interview-sheet/${sheetId}`,
      data
    );
    return response.data;
  },

  // Finalize interview sheet
  finalize: async (sheetId: string): Promise<{ success: boolean; status: string; completed_at: string; updated_at: string }> => {
    const response = await apiClient.post<{ success: boolean; status: string; completed_at: string; updated_at: string }>(
      `/interview-sheet/${sheetId}/finalize`
    );
    return response.data;
  },
};
