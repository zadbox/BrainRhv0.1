// Types pour l'API Brain RH

export interface Contact {
  nom_complet: string;
  poste?: string;
  email: string;
  telephone?: string;
  canal_prefere?: 'email' | 'telephone' | 'slack' | 'autre';
  notes?: string;
}

export interface Enterprise {
  id: string;
  nom: string;
  site_web?: string;
  secteur?: string;
  notes?: string;
  contacts: Contact[];
  created_at?: string;
  last_modified?: string;
  projects_count: number;
}

export interface Project {
  id: string;
  nom: string;
  enterprise_id?: string;
  service_demandeur?: string;
  responsable_offre?: string;
  contact_responsable?: string;
  notes?: string;
  description?: string;
  created_at: string;
  last_modified: string;
  status: 'actif' | 'archive';
  updated_at?: string;
}

export type CVExperience = Record<string, unknown>;
export type CVFormation = Record<string, unknown>;
export type CVProjectItem = Record<string, unknown> | string;

export interface CV {
  cv: string;
  project_id?: string;
  enterprise_id?: string;
  enterprise_nom?: string;
  identite?: {
    nom?: string;
    prenom?: string;
    email?: string;
    telephone?: string;
    adresse?: string;
  };
  titre?: string;
  resume_professionnel?: string;
  competences_techniques: string[];
  competences_transversales: string[];
  langues: string[];
  experience?: Array<{
    entreprise?: string;
    poste?: string;
    date_debut?: string;
    date_fin?: string;
    description?: string;
  }>;
  experiences_professionnelles: CVExperience[];
  formations: CVFormation[];
  certifications: string[];
  projets: CVProjectItem[];
}

export interface Offre {
  sections: {
    titre?: string;
    description?: string;
    competences_techniques: string[];
    competences_transversales: string[];
    langues: string[];
    experiences_professionnelles: CVExperience[];
    formations: CVFormation[];
    certifications: string[];
    projets: CVProjectItem[];
  };
  must_have: string[];
  nice_have: string[];
}

export interface Evidence {
  id: string;
  type: 'section' | 'json_path' | 'quote' | string;
  ref: string;
}

export interface EvidenceMap {
  commentaire_scoring?: string[];
  appreciation_globale?: string[];
}

export interface Gap {
  period: string;
  duration_months: number;
  between: string;
}

export interface Overlap {
  overlap_period: string;
  overlap_days: number;
  experiences: string;
  same_company: boolean;
}

export interface Flags {
  gappes?: Gap[];
  overlaps?: Overlap[];
}

export interface ResultatMatching {
  cv: string;
  candidate_name?: string;
  score_final: number;
  score_base: number;
  bonus_nice_have_multiplicateur: number;
  coefficient_qualite_experience: number;
  nice_have_manquants: string[];
  commentaire_scoring?: string;
  appreciation_globale?: string;
  evidences?: Evidence[];
  evidence_map?: EvidenceMap;
  flags?: Flags;
  original_cv_url?: string | null;
}

export interface MatchingResponse {
  results: ResultatMatching[];
  metadata: {
    total_cvs: number;
    filtered_must_have: number;
    top_reranked: number;
    duree_totale_s: number;
    timestamp?: string;
  };
}

export interface CVParseResult {
  success: boolean;
  cv?: string;
  filename?: string;
  data?: CV;
  error?: string;
}

export interface CVParseResponse {
  success_count: number;
  failed_count: number;
  total: number;
  duree_totale_s: number;
  results: CVParseResult[];
}

// SSE Events
export interface SSEProgressEvent {
  step: string;
  current: number;
  total: number;
  progress: number;
  message: string;
}

export interface SSEResultEvent {
  success: boolean;
  cv?: string;
  data?: unknown;
  error?: string;
}

export interface SSEDoneEvent {
  summary: {
    results?: unknown[];
    metadata?: Record<string, unknown>;
    success_count?: number;
    failed_count?: number;
    total?: number;
  };
}

export interface SSEErrorEvent {
  code: string;
  message: string;
  traceback?: string;
}

export interface APIError {
  code: string;
  message: string;
  details?: unknown;
}

export interface ProjectHistory {
  total: number;
  items: {
    matching_id: string;
    timestamp: string;
    candidats_count: number;
  }[];
}

// Enrichissement d'offres
export interface EnrichmentCompetence {
  name: string;
  type: 'must' | 'nice';
  source: string;
  rationale: string;
}

export interface EnrichmentItem {
  name: string;
  rationale: string;
}

export interface EnrichmentMission {
  text: string;
  rationale: string;
}

export interface EnrichmentPropositions {
  competences: EnrichmentCompetence[];
  outils: EnrichmentItem[];
  langages: EnrichmentItem[];
  certifications: EnrichmentItem[];
  missions: EnrichmentMission[];
  questions_clarification: string[];
}

export interface EnrichmentResult {
  coverage_score: number;
  propositions: EnrichmentPropositions;
}

export interface EnrichmentSelections {
  competences: number[];
  outils: number[];
  langages: number[];
  certifications: number[];
  missions: number[];
}

export interface QuestionResponses {
  [question: string]: string;
}
