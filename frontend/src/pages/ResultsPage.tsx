import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Eye, BarChart3, Calendar, ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select } from '../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { LoadingPage } from '../components/shared/Loading';
import { ErrorBanner } from '../components/shared/ErrorBanner';
import { EmptyState } from '../components/shared/EmptyState';
import { projectsApi } from '../api/projects';
import type { Project, APIError, ProjectHistory } from '../api/types';

export const ResultsPage: React.FC = () => {
  const { projectId: projectIdFromUrl } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>(projectIdFromUrl || '');
  const [matchingHistory, setMatchingHistory] = useState<ProjectHistory | null>(null);
  const [dateFilter, setDateFilter] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<APIError | null>(null);

  const fetchProjects = async () => {
    try {
      const data = await projectsApi.getAll();
      setProjects(data);
    } catch (err) {
      console.error('Failed to fetch projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchMatchingHistory = async (projectId: string) => {
    try {
      setLoading(true);
      setError(null);
      const history = await projectsApi.getHistory(projectId);
      setMatchingHistory(history);
    } catch (err) {
      setError(err as APIError);
      setMatchingHistory(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      fetchMatchingHistory(selectedProjectId);
    } else {
      setMatchingHistory(null);
    }
  }, [selectedProjectId]);

  const filteredHistory = matchingHistory?.items.filter((item) => {
    if (!dateFilter) return true;
    const itemDate = item.timestamp.split('_')[0];
    return itemDate.includes(dateFilter);
  }) || [];

  const formatTimestampLabel = (timestamp?: string) => {
    if (!timestamp) return '—';
    const [datePart, timePart] = timestamp.split('_');
    if (!datePart || !timePart) return timestamp.replace('_', ' · ');
    const isoString = `${datePart}T${timePart.replace(/-/g, ':')}`;
    const date = new Date(isoString);
    if (!Number.isNaN(date.getTime())) {
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    }
    return `${datePart} · ${timePart.replace(/-/g, ':')}`;
  };

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedProjectId),
    [projects, selectedProjectId]
  );

  const heroGradient = 'from-[#7f8bff] via-[#8ed4ff] to-[#53f4c8]';
  const totalRuns = matchingHistory?.total ?? 0;
  const latestHistoryEntry = matchingHistory?.items?.[0];
  const lastRunLabel = latestHistoryEntry ? formatTimestampLabel(latestHistoryEntry.timestamp) : 'No runs yet';
  const latestCandidatesLabel = latestHistoryEntry ? `${latestHistoryEntry.candidats_count} resumes` : '—';
  const totalCandidates =
    matchingHistory?.items.reduce((acc, item) => acc + (item.candidats_count || 0), 0) ?? 0;
  const heroTitle = selectedProject
    ? `Matching history – ${selectedProject.nom}`
    : 'Matching results archive';
  const heroDescription = selectedProject
    ? 'Review every run delivered by the AI matching pipeline for this project.'
    : 'Select a project to explore its historical matching runs and share insights with stakeholders.';
  const heroBadge = selectedProject ? `${totalRuns} run(s)` : 'History overview';
  const projectMetricLabel = selectedProject ? selectedProject.nom : 'Select a project';
  const enterpriseMetricLabel = selectedProject?.enterprise_id ?? '—';

  if (loading && !selectedProjectId) return <LoadingPage text="Loading projects..." />;

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
                Results cockpit
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <Badge variant="secondary" className="bg-white/20 text-black">
                {heroBadge}
              </Badge>
              {selectedProjectId && (
                <div className="flex flex-wrap items-center gap-2">
                  <Button
                    variant="outline"
                    className="border-black/30 bg-black/10 text-black hover:bg-black/20"
                    onClick={() => navigate(`/projects/${selectedProjectId}`)}
                  >
                    View project
                  </Button>
                  <Button
                    className="bg-black text-white hover:bg-black/80"
                    onClick={() => navigate(`/projects/${selectedProjectId}/matching`)}
                  >
                    Jump to matching
                  </Button>
                </div>
              )}
            </div>
          </div>
          <div className="space-y-4">
            <h1 className="text-4xl font-semibold tracking-tight text-black">{heroTitle}</h1>
            <p className="max-w-2xl text-base text-black/70">{heroDescription}</p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl border border-black/10 bg-black/5 p-4">
              <p className="text-xs uppercase tracking-widest text-black/50">Project</p>
              <p className="mt-2 text-lg font-semibold text-black">{projectMetricLabel}</p>
            </div>
            <div className="rounded-2xl border border-black/10 bg-black/5 p-4">
              <p className="text-xs uppercase tracking-widest text-black/50">Company</p>
              <p className="mt-2 text-lg font-semibold text-black">{enterpriseMetricLabel}</p>
            </div>
            <div className="rounded-2xl border border-black/10 bg-black/5 p-4">
              <p className="text-xs uppercase tracking-widest text-black/50">Runs completed</p>
              <p className="mt-2 text-lg font-semibold text-black">{totalRuns}</p>
            </div>
            <div className="rounded-2xl border border-black/10 bg-black/5 p-4">
              <p className="text-xs uppercase tracking-widest text-black/50">Latest run</p>
              <p className="mt-2 text-lg font-semibold text-black">{lastRunLabel}</p>
            </div>
          </div>
        </div>
      </div>

      {error && <ErrorBanner error={error} />}

      {!projectIdFromUrl && (
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-white/5 bg-white/[0.04] p-6">
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-widest text-white/50">Project scope</p>
            <p className="text-sm text-white/60">Select a project to explore its complete matching history.</p>
          </div>
          <div className="w-full min-w-[220px] max-w-xs">
            <Label htmlFor="project-select" className="sr-only">
              Project
            </Label>
            <Select
              id="project-select"
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="border-white/20 bg-white text-slate-900 focus:border-white/40"
            >
              <option value="">Select a project</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.nom}
                </option>
              ))}
            </Select>
          </div>
        </div>
      )}

      {selectedProjectId && matchingHistory && (
        <div className="space-y-6 rounded-3xl border border-white/5 bg-white/[0.03] p-8 backdrop-blur-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-semibold text-white">Matching history</h2>
              <p className="text-white/70">
                {totalRuns} run(s) · {totalCandidates} resume(s) analysed · Latest: {latestCandidatesLabel}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-white/60" />
              <Input
                type="date"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
                placeholder="Filter by date"
                className="w-auto border-white/20 bg-white text-slate-900 focus:border-white/40"
              />
            </div>
          </div>

          {filteredHistory.length === 0 ? (
            <EmptyState
              icon={BarChart3}
              title="No matching runs"
              description="No matching run found for this filter"
            />
          ) : (
            <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04]">
              <Table>
                <TableHeader>
                  <TableRow className="border-white/10">
                    <TableHead className="text-white/70">Date & time</TableHead>
                    <TableHead className="text-white/70">Candidates</TableHead>
                    <TableHead className="text-right text-white/70">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredHistory.map((item) => (
                    <TableRow
                      key={item.matching_id}
                      className="cursor-pointer border-white/10 hover:bg-white/[0.08]"
                      onClick={() => navigate(`/projects/${selectedProjectId}/results/${item.matching_id}`)}
                    >
                      <TableCell className="font-mono text-sm text-white">
                        {formatTimestampLabel(item.timestamp)}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="bg-white/15 text-white">
                          {item.candidats_count} resumes
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end">
                          <Eye className="h-4 w-4 text-white/70" />
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      )}

      {selectedProjectId && !matchingHistory && !loading && (
        <div className="rounded-3xl border border-white/5 bg-white/[0.03] p-10">
          <EmptyState
            icon={BarChart3}
            title="No history available"
            description="No matching runs recorded for this project yet."
          />
        </div>
      )}

      {!selectedProjectId && !projectIdFromUrl && projects.length === 0 && (
        <div className="rounded-3xl border border-white/5 bg-white/[0.03] p-10">
          <EmptyState
            icon={BarChart3}
            title="No projects available"
            description="Create a project before consulting matching history."
          />
        </div>
      )}
    </div>
  );
};
