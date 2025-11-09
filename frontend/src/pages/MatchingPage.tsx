import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import type { ChangeEvent } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Target, Play, Clock, CheckCircle2, History, FileText, ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select } from '../components/ui/select';
import { Progress } from '../components/ui/progress';
import { Badge } from '../components/ui/badge';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from '../components/ui/card';
import { LoadingPage } from '../components/shared/Loading';
import { ErrorBanner } from '../components/shared/ErrorBanner';
import { EmptyState } from '../components/shared/EmptyState';
import { EvidencePanel } from '../components/matching/EvidencePanel';
import { renderTextWithEvidences } from '../components/matching/renderTextWithEvidences';
import { InterviewSheetButton } from '../components/interview/InterviewSheetButton';
import { useSSE } from '../hooks/useSSE';
import type { SSEMessage } from '../hooks/useSSE';
import { matchingApi } from '../api/matching';
import { projectsApi } from '../api/projects';
import { enterprisesApi } from '../api/enterprises';
import { API_BASE_URL } from '../api/client';
import type { Project, APIError, SSEProgressEvent, SSEDoneEvent, Enterprise, ResultatMatching, MatchingResponse } from '../api/types';

interface MatchingStep {
  name: string;
  progress: number;
  message: string;
  completed: boolean;
}

const initialSteps: MatchingStep[] = [
  { name: 'Must-have filtering', progress: 0, message: 'Waiting...', completed: false },
  { name: 'Similarity & nice-to-have scoring', progress: 0, message: 'Waiting...', completed: false },
  { name: 'LLM re-ranking', progress: 0, message: 'Waiting...', completed: false },
];

interface MatchingSummary {
  results?: ResultatMatching[];
  metadata?: MatchingResponse['metadata'];
  success_count?: number;
  failed_count?: number;
  total?: number;
}

export const MatchingPage: React.FC = () => {
  const { projectId: projectIdFromUrl } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>(projectIdFromUrl || '');
  const [enterprises, setEnterprises] = useState<Enterprise[]>([]);
  const [selectedEnterpriseId, setSelectedEnterpriseId] = useState<string>('');
  const [topN, setTopN] = useState<number>(10);
  const model = 'gpt-5-mini'; // Fixed model (no user choice)
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<APIError | null>(null);
  const [running, setRunning] = useState(false);
  const [steps, setSteps] = useState<MatchingStep[]>(initialSteps);
  const [results, setResults] = useState<MatchingSummary | null>(null);
  const [startTime, setStartTime] = useState<number | null>(null);
  const [endTime, setEndTime] = useState<number | null>(null);

  // State to force timer re-render
  const [, setTick] = useState(0);

  // 🔑 Unique runId for server idempotency
  const runIdRef = useRef<string>('');
  if (!runIdRef.current) {
    runIdRef.current = crypto.randomUUID();
  }

  // Update timer every 100ms while matching is running
  useEffect(() => {
    if (!running || !startTime) return;

    const interval = setInterval(() => {
      setTick(prev => prev + 1);
    }, 100); // Update every 100ms for smooth display

    return () => clearInterval(interval);
  }, [running, startTime]);

  const handleMessage = useCallback((event: SSEMessage) => {
    if (event.type === 'progress') {
      const progressData = event.data as SSEProgressEvent;
      setSteps((prev) => {
        const newSteps = [...prev];
        const stepMap: Record<string, number> = {
          'must_have_filtering': 0,
          'embedding': 1,
          'reranking': 2,
        };
        const stepIndex = stepMap[progressData.step.toLowerCase()];
        if (stepIndex !== undefined && newSteps[stepIndex]) {
          newSteps[stepIndex] = {
            ...newSteps[stepIndex],
            progress: (progressData.progress || 0) * 100,
            message: progressData.message || '',
            completed: (progressData.progress || 0) >= 1.0,
          };
        }
        return newSteps;
      });
    } else if (event.type === 'done') {
      const doneData = event.data as SSEDoneEvent;
      setResults(doneData.summary as MatchingSummary);
      setRunning(false);
      setEndTime(Date.now());
      // Only mark steps at 100% if they actually progressed
      setSteps((prev) => prev.map((s) => {
        if (s.progress > 0) {
          return { ...s, completed: true, progress: 100 };
        }
        return s;
      }));

      // No auto-redirect – display results on the same page
    } else if (event.type === 'error') {
      const errorData = event.data as APIError;
      setError(errorData);
      setRunning(false);
      setEndTime(Date.now());
    }
  }, []);

  // 📡 SSE URL with runId for server-side idempotency
  const streamUrl = useMemo(() => {
    if (!running || !selectedProjectId) return '';
    const baseUrl = matchingApi.getRunStreamUrl(selectedProjectId, topN, model);
    return `${baseUrl}&runId=${runIdRef.current}`;
  }, [running, selectedProjectId, topN, model]);

  const { close } = useSSE({
    url: streamUrl,
    enabled: running,
    onMessage: handleMessage,
    onError: (err) => {
      console.error('[MatchingPage] SSE Error:', err);
      setError({ code: 'SSE_ERROR', message: 'Connection lost with the server' });
      setRunning(false);
    },
    closeOn: ['done', 'error'], // Auto-close when matching is finished
    forceSingle: false, // Temporarily disabled for debugging
  });

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const data = await projectsApi.getAll();
      setProjects(data);
    } catch (err) {
      setError(err as APIError);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    const loadEnterprises = async () => {
      try {
        const data = await enterprisesApi.getAll();
        setEnterprises(data);
      } catch (err) {
        setError(err as APIError);
      }
    };

    loadEnterprises();
  }, []);

  const handleStartMatching = () => {
    if (!selectedProjectId) {
      setError({ code: 'VALIDATION_ERROR', message: 'Please select a project' });
      return;
    }

    // 🔄 Generate a new runId for each run
    runIdRef.current = crypto.randomUUID();
    console.log(`[MatchingPage] New matching run with runId: ${runIdRef.current}`);

    setError(null);
    setResults(null);
    setSteps(initialSteps);
    setStartTime(Date.now());
    setEndTime(null);
    setRunning(true);
  };

  const handleStop = () => {
    close();
    setRunning(false);
    setEndTime(Date.now());
  };

  const activeProjectId = selectedProjectId || projectIdFromUrl || '';

  const filteredProjects = useMemo(() => {
    if (!selectedEnterpriseId) {
      return projects;
    }
    return projects.filter((project) => project.enterprise_id === selectedEnterpriseId);
  }, [projects, selectedEnterpriseId]);

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === activeProjectId),
    [projects, activeProjectId]
  );

  const selectedEnterprise = useMemo(() => {
    const enterpriseId = selectedEnterpriseId || selectedProject?.enterprise_id;
    if (!enterpriseId) return undefined;
    return enterprises.find((enterprise) => enterprise.id === enterpriseId);
  }, [enterprises, selectedEnterpriseId, selectedProject?.enterprise_id]);

  useEffect(() => {
    if (!selectedProject?.enterprise_id) {
      return;
    }

    setSelectedEnterpriseId((prev) => {
      const enterpriseId = selectedProject.enterprise_id;
      if (!enterpriseId) {
        return prev;
      }
      if (prev === enterpriseId) {
        return prev;
      }
      return enterpriseId;
    });
  }, [selectedProject?.enterprise_id]);

  const companyLabel = selectedEnterprise?.nom ?? 'Select a company';
  const projectLabel = selectedProject?.nom
    ? selectedProject.nom
    : filteredProjects.length > 0
    ? 'Select a project'
    : selectedEnterpriseId
    ? 'No project available'
    : 'Select a project';

  const handleEnterpriseChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    setSelectedEnterpriseId(value);

    if (!value) {
      setSelectedProjectId('');
      return;
    }

    const currentProject = projects.find((project) => project.id === selectedProjectId);
    if (currentProject && currentProject.enterprise_id !== value) {
      setSelectedProjectId('');
    }
  };

  const handleProjectChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    setSelectedProjectId(value);

    if (!value) {
      return;
    }

    const project = projects.find((item) => item.id === value);
    if (project?.enterprise_id) {
      setSelectedEnterpriseId(project.enterprise_id);
    }
  };

  const handleTopNChange = (event: ChangeEvent<HTMLInputElement>) => {
    const next = Math.min(Math.max(parseInt(event.target.value, 10) || 1, 1), 10);
    setTopN(next);
  };

  const duration = startTime && endTime ? ((endTime - startTime) / 1000).toFixed(1) : null;
  const matchedCandidates = results?.results?.length ?? 0;
  const heroGradient = running
    ? 'from-[#5b7bff] via-[#7ec8ff] to-[#4df2c6]'
    : matchedCandidates > 0
    ? 'from-[#5f88ff] via-[#8ed4ff] to-[#53f4c8]'
    : 'from-[#7f8bff] via-[#8ed4ff] to-[#53f4c8]';
  const heroBadge = running ? 'Live run' : matchedCandidates > 0 ? `${matchedCandidates} candidate(s)` : 'Awaiting launch';
  const heroStatus = running
    ? 'We are orchestrating the AI-driven matching workflow in real time.'
    : matchedCandidates > 0
    ? 'Your latest run is ready to review and share with hiring stakeholders.'
    : 'Calibrate your scope and launch the enriched matching experience.';
  const lastDuration = duration || results?.metadata?.duree_totale_s?.toFixed(1) || null;

  if (loading) return <LoadingPage text="Loading projects..." />;

  return (
    <div className="space-y-10 rounded-3xl bg-[#0c0c12] p-10 text-gray-100 shadow-[0_45px_140px_-90px_rgba(90,80,255,0.7)]">
      <div className={`relative overflow-hidden rounded-3xl bg-gradient-to-br ${heroGradient} p-10 text-black shadow-[0px_20px_60px_-30px_rgba(90,140,255,0.6)]`}>
        <span className="absolute -top-28 -right-16 h-56 w-56 rounded-full bg-white/25 blur-3xl" aria-hidden="true" />
        <span className="absolute bottom-[-80px] left-[-60px] h-72 w-72 rounded-full bg-white/20 blur-3xl" aria-hidden="true" />
        <div className="relative space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="icon"
                className="border-black/30 bg-black/10 text-black hover:bg-black/20"
                onClick={() => navigate(-1)}
                aria-label="Go back"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div className="inline-flex items-center gap-2 rounded-full bg-black/10 px-4 py-1 text-xs font-semibold uppercase tracking-widest text-black/70">
                AI matching cockpit
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="bg-white/20 text-black">
                {heroBadge}
              </Badge>
              {(projectIdFromUrl || selectedProjectId) && (
                <Button
                  size="icon"
                  variant="outline"
                  className="border-black/20 bg-black/10 text-black hover:bg-black/20"
                  aria-label="View results history"
                  onClick={() => navigate(`/projects/${projectIdFromUrl || selectedProjectId}/results`)}
                >
                  <History className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
          <div className="space-y-4">
            <h1 className="text-4xl font-semibold tracking-tight text-black">Matching control center</h1>
            <p className="max-w-2xl text-base text-black/70">{heroStatus}</p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl border border-black/10 bg-black/5 p-4">
              <p className="text-xs uppercase tracking-widest text-black/50">Company</p>
              <p className="mt-2 text-lg font-semibold text-black">{companyLabel}</p>
            </div>
            <div className="rounded-2xl border border-black/10 bg-black/5 p-4">
              <p className="text-xs uppercase tracking-widest text-black/50">Project</p>
              <p className="mt-2 text-lg font-semibold text-black">{projectLabel}</p>
            </div>
            <div className="rounded-2xl border border-black/10 bg-black/5 p-4">
              <p className="text-xs uppercase tracking-widest text-black/50">Top candidates</p>
              <p className="mt-2 text-lg font-semibold text-black">{topN}</p>
            </div>
            <div className="rounded-2xl border border-black/10 bg-black/5 p-4">
              <p className="text-xs uppercase tracking-widest text-black/50">Last duration</p>
              <p className="mt-2 text-lg font-semibold text-black">{lastDuration ? `${lastDuration}s` : '—'}</p>
            </div>
          </div>
        </div>
      </div>

      {error && <ErrorBanner error={error} />}

      {!running && !results && (
        projects.length === 0 ? (
          <EmptyState
            icon={Target}
            title="No projects available"
            description="Create a project before launching a matching run"
          />
        ) : (
          <div className="grid gap-8 xl:grid-cols-[1.2fr_0.8fr]">
            <Card className="border border-white/5 bg-white/[0.05] text-white">
              <CardHeader>
                <CardTitle>Configure your run</CardTitle>
                <CardDescription className="text-white/70">
                  Choose the mandate and calibrate the reranking scope before launching the AI workflow.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="enterprise-select" className="text-sm font-medium text-white/80">
                      Company *
                    </Label>
                    <Select
                      id="enterprise-select"
                      value={selectedEnterpriseId}
                      onChange={handleEnterpriseChange}
                      className="border-white/20 bg-white text-slate-900 focus:border-white/40"
                    >
                      <option value="">Select a company</option>
                      {enterprises.map((enterprise) => (
                        <option key={enterprise.id} value={enterprise.id}>
                          {enterprise.nom}
                        </option>
                      ))}
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="project-select" className="text-sm font-medium text-white/80">
                      Project *
                    </Label>
                    <Select
                      id="project-select"
                      value={selectedProjectId}
                      onChange={handleProjectChange}
                      className="border-white/20 bg-white text-slate-900 focus:border-white/40"
                    >
                      <option value="">Select a project</option>
                      {filteredProjects.map((project) => (
                        <option key={project.id} value={project.id}>
                          {project.nom}
                        </option>
                      ))}
                    </Select>
                    {selectedEnterpriseId && filteredProjects.length === 0 && (
                      <p className="text-xs text-white/60">No project available for this company yet.</p>
                    )}
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="top-n" className="text-sm font-medium text-white/80">
                      Top N (reranking)
                    </Label>
                    <Input
                      id="top-n"
                      type="number"
                      min={1}
                      max={10}
                      value={topN}
                      onChange={handleTopNChange}
                      className="border-white/20 bg-white/[0.12] text-white placeholder:text-white/40"
                    />
                    <p className="text-xs text-white/60">
                      Number of resumes reranked (max: 10)
                    </p>
                  </div>

                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/70">
                    <p className="font-semibold text-white">AI model</p>
                    <p className="mt-1">BRAIN MODEL</p>
                    <p className="mt-3 text-xs uppercase tracking-widest text-white/50">
                      Fixed to ensure consistent scoring
                    </p>
                  </div>
                </div>

                <Button
                  onClick={handleStartMatching}
                  size="lg"
                  className="w-full bg-white text-black hover:bg-white/90"
                  disabled={running}
                >
                  <Play className="mr-2 h-5 w-5" />
                  Start matching
                </Button>
              </CardContent>
            </Card>

            <div className="rounded-3xl border border-white/5 bg-white/[0.03] p-8 backdrop-blur-sm">
              <div className="flex items-center gap-3 text-sm font-medium uppercase tracking-widest text-white/60">
                <Target className="h-4 w-4" />
                Run insights
              </div>
              <div className="mt-6 space-y-5 text-sm text-white/70">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="mt-1 h-4 w-4 text-emerald-300" />
                  <div>
                    <p className="font-semibold text-white">Structured prerequisites</p>
                    <p>Ensure must-have criteria and job context are aligned with the hiring team.</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Clock className="mt-1 h-4 w-4 text-white/60" />
                  <div>
                    <p className="font-semibold text-white">Live progress tracking</p>
                    <p>Monitor filtering, semantic scoring and reranking as the pipeline executes.</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <History className="mt-1 h-4 w-4 text-white/60" />
                  <div>
                    <p className="font-semibold text-white">Instant replays</p>
                    <p>Access previous runs and share curated shortlists with stakeholders in one click.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )
      )}

      {/* Progress */}
      {running && (
        <div className="grid gap-8 xl:grid-cols-[1.1fr_0.9fr]">
          <Card className="border border-white/5 bg-white/[0.05] text-white">
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <CardTitle>Matching in progress</CardTitle>
                  <CardDescription className="text-white/70">
                    The analysis may take several minutes depending on the number of resumes.
                  </CardDescription>
                </div>
                <Button variant="destructive" onClick={handleStop}>
                  Stop
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {startTime && (
                <div className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.05] p-4 text-sm text-white/70">
                  <Clock className="h-4 w-4" />
                  <span>Elapsed time: {((Date.now() - startTime) / 1000).toFixed(1)}s</span>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="space-y-3">
            {steps.map((step, index) => (
              <Card key={index} className="border border-white/5 bg-white/[0.03] text-white">
                <CardContent className="pt-6">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {step.completed ? (
                          <CheckCircle2 className="h-5 w-5 text-emerald-300" />
                        ) : (
                          <div className="h-5 w-5 rounded-full border-2 border-white/40" />
                        )}
                        <span className="font-medium text-white">{step.name}</span>
                      </div>
                      <Badge
                        variant={step.completed ? 'success' : 'secondary'}
                        className={step.completed ? 'bg-emerald-400/20 text-emerald-100' : 'bg-white/10 text-white'}
                      >
                        {Math.round(step.progress)}%
                      </Badge>
                    </div>
                    <p className="pl-8 text-sm text-white/60">{step.message}</p>
                    <div className="px-8">
                      <Progress value={step.progress} max={100} className="w-full" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Results Summary + Detailed Results */}
      {results && !running && (
        <div className="space-y-8">
          <Card className="border border-white/5 bg-white/[0.05] text-white">
            <CardHeader>
              <CardTitle>Matching results</CardTitle>
              <CardDescription className="text-white/70">
                {matchedCandidates} candidate(s) ranked by final score
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {(results.metadata?.filtered_must_have === 0 || results.results?.length === 0) && (
                <div className="rounded-2xl border border-amber-400/40 bg-amber-500/10 p-4 text-amber-200">
                  <div className="flex items-start gap-3">
                    <div className="text-amber-300">
                      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h3 className="mb-1 font-semibold text-amber-100">No resume selected</h3>
                      <p className="text-sm text-amber-100/80">
                        The {results.metadata?.total_cvs || 0} analysed resumes were removed during the must-have filtering.
                        No candidate matches the mandatory criteria defined in the job offer.
                      </p>
                      <p className="mt-2 text-sm font-medium text-amber-100">
                        💡 Tip: Review the offer's must-have criteria or add more resumes.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-widest text-white/60">Resumes analysed</p>
                  <p className="mt-2 text-2xl font-semibold text-white">{results.metadata?.total_cvs || 0}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-widest text-white/60">Must-have validated</p>
                  <p className={`mt-2 text-2xl font-semibold ${results.metadata?.filtered_must_have === 0 ? 'text-red-300' : 'text-white'}`}>
                    {results.metadata?.filtered_must_have || 0}
                  </p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-widest text-white/60">Top reranked</p>
                  <p className="mt-2 text-2xl font-semibold text-white">{results.metadata?.top_reranked || 0}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-widest text-white/60">Duration</p>
                  <p className="mt-2 text-2xl font-semibold text-white">{lastDuration ? `${lastDuration}s` : '0s'}</p>
                </div>
              </div>

              <Button
                onClick={() => {
                  setResults(null);
                  setSteps(initialSteps);
                  setStartTime(null);
                  setEndTime(null);
                }}
                variant="outline"
                className="w-full border-white/20 text-white hover:bg-white/10"
              >
                New matching run
              </Button>
            </CardContent>
          </Card>

          {results.results && results.results.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">Candidate ranking</h2>
              {results.results.map((cv: ResultatMatching, index: number) => {
                const isRerankFallback = cv.commentaire_scoring?.includes('⚠️ Re-ranking LLM indisponible');

                return (
                  <Card
                    key={index}
                    className={`border-white/5 bg-white/[0.04] text-white ${isRerankFallback ? 'border-orange-400/40' : ''}`}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <CardTitle className="flex items-center gap-2 text-white">
                            <span className="text-white/60">#{index + 1}</span>
                            <span>{cv.cv}</span>
                            {isRerankFallback && (
                              <Badge variant="outline" className="ml-2 border-orange-400 text-orange-200">
                                ⚠️ Reranking unavailable
                              </Badge>
                            )}
                          </CardTitle>
                          <CardDescription className="text-white/70">
                            Final score: {cv.score_final.toFixed(3)}
                          </CardDescription>
                        </div>
                        <div className="flex gap-2">
                          {cv.original_cv_url && (
                            <a
                              href={`${API_BASE_URL}${cv.original_cv_url}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-block"
                            >
                              <Button variant="ghost" size="icon" className="h-8 w-8 text-white hover:bg-white/10">
                                <FileText className="h-4 w-4" />
                              </Button>
                            </a>
                          )}
                          {selectedProjectId && results.metadata?.timestamp && (
                            <InterviewSheetButton
                              candidateId={cv.cv}
                              jobId={selectedProjectId}
                              matchingId={results.metadata.timestamp}
                              variant="outline"
                              size="sm"
                            />
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-5">
                      <div className="grid gap-4 md:grid-cols-4">
                        <div>
                          <p className="text-xs uppercase tracking-widest text-white/60">Final score</p>
                          <p className="mt-1 text-xl font-semibold text-white">{cv.score_final.toFixed(3)}</p>
                        </div>
                        <div>
                          <p className="text-xs uppercase tracking-widest text-white/60">Base score</p>
                          <p className="mt-1 text-xl font-semibold text-white">{cv.score_base.toFixed(3)}</p>
                        </div>
                        <div>
                          <p className="text-xs uppercase tracking-widest text-white/60">Nice-to-have multiplier</p>
                          <p className="mt-1 text-xl font-semibold text-white">{cv.bonus_nice_have_multiplicateur.toFixed(3)}</p>
                          {cv.nice_have_manquants?.length > 0 && (
                            <p className="text-xs text-orange-300">{cv.nice_have_manquants.length} missing</p>
                          )}
                        </div>
                        <div>
                          <p className="text-xs uppercase tracking-widest text-white/60">Experience quality</p>
                          <p className="mt-1 text-xl font-semibold text-emerald-200">{cv.coefficient_qualite_experience.toFixed(2)}</p>
                        </div>
                      </div>

                      {cv.nice_have_manquants && cv.nice_have_manquants.length > 0 && (
                        <div>
                          <p className="mb-2 text-sm font-semibold text-orange-200">Missing nice-to-haves</p>
                          <div className="flex flex-wrap gap-2">
                            {cv.nice_have_manquants.map((item: string, idx: number) => (
                              <Badge key={idx} variant="outline" className="border-orange-400 text-orange-200">
                                {item}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {cv.commentaire_scoring && (
                        <div>
                          <p className="mb-2 text-sm font-semibold text-white">Scoring analysis</p>
                          <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/80 whitespace-pre-wrap">
                            {renderTextWithEvidences(cv.commentaire_scoring, cv.evidences)}
                          </div>
                        </div>
                      )}

                      {cv.appreciation_globale && (
                        <div>
                          <p className="mb-2 text-sm font-semibold text-white">HR appreciation</p>
                          <div className="rounded-2xl border border-blue-200/40 bg-blue-500/10 p-4 text-sm text-white/85 whitespace-pre-wrap">
                            {renderTextWithEvidences(cv.appreciation_globale, cv.evidences)}
                          </div>
                        </div>
                      )}

                      <EvidencePanel evidences={cv.evidences} flags={cv.flags} />

                      {isRerankFallback && (
                        <div className="rounded-2xl border border-orange-400/40 bg-orange-500/10 p-4 text-sm text-orange-100">
                          <strong>ℹ️ Note:</strong> The qualitative HR analysis could not be generated because the reranking service failed.
                          Quantitative scores remain valid with a neutral quality coefficient.
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}

      {!running && !results && projects.length === 0 && (
        <EmptyState
          icon={Target}
          title="No projects available"
          description="Create a project before launching a matching run"
        />
      )}

      {/* Results history button - always visible at the bottom */}
    </div>
  );
};
