import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
  ArrowLeft,
  Building2,
  Briefcase,
  CheckCircle2,
  ShieldCheck,
  UserCircle,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { LoadingPage } from '../components/shared/Loading';
import { ErrorBanner } from '../components/shared/ErrorBanner';
import { projectsApi } from '../api/projects';
import { enterprisesApi } from '../api/enterprises';
import { offresApi } from '../api/offres';
import { cvsApi } from '../api/cvs';
import type { Project, Offre, CV, APIError, Enterprise } from '../api/types';
import { useToast } from '../hooks/useToast';

export const ProjectDetailPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { error: showError } = useToast();
  const refreshRequested = location.state?.refreshData;

  const [project, setProject] = useState<Project | null>(null);
  const [offre, setOffre] = useState<Offre | null>(null);
  const [cvs, setCvs] = useState<CV[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<APIError | null>(null);
  const [enterprises, setEnterprises] = useState<Enterprise[]>([]);

  const fetchData = useCallback(async () => {
    if (!projectId) return;

    try {
      setLoading(true);
      setError(null);

      const projectData = await projectsApi.getById(projectId);
      setProject(projectData);

      try {
        const offreData = await offresApi.getByProject(projectId);
        setOffre(offreData);
      } catch {
        setOffre(null);
      }

      try {
        const cvsData = await cvsApi.getByProject(projectId);
        setCvs(cvsData);
      } catch {
        setCvs([]);
      }
    } catch (err) {
      setError(err as APIError);
      showError('Error', 'Unable to load the project');
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const fetchEnterprises = async () => {
    try {
      const data = await enterprisesApi.getAll();
      setEnterprises(data);
    } catch (err) {
      console.error('Failed to fetch enterprises:', err);
    }
  };

  useEffect(() => {
    fetchEnterprises();
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (refreshRequested) {
      fetchData();
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [refreshRequested, fetchData, navigate, location.pathname]);

  if (loading) return <LoadingPage text="Loading project..." />;
  if (!project) return <div>Project not found</div>;

  const isArchived = project.status === 'archive';
  const offerReady = Boolean(offre);
  const cvsReady = cvs.length > 0;
  const canLaunchMatching = offerReady && cvsReady && !isArchived;
  const heroGradient = isArchived
    ? 'from-[#525868] via-[#6d7491] to-[#3a3f52]'
    : 'from-[#7f8bff] via-[#8ed4ff] to-[#53f4c8]';

  return (
    <div className="space-y-10 rounded-3xl bg-[#0c0c12] p-10 text-gray-100 shadow-[0_45px_140px_-90px_rgba(90,80,255,0.7)]">
      <div className={`relative overflow-hidden rounded-3xl bg-gradient-to-br ${heroGradient} p-10 text-black shadow-[0px_20px_60px_-30px_rgba(90,140,255,0.6)]`}>
        <span className="absolute -top-28 -right-16 h-56 w-56 rounded-full bg-white/25 blur-3xl" aria-hidden="true" />
        <span className="absolute bottom-[-80px] left-[-60px] h-72 w-72 rounded-full bg-white/20 blur-3xl" aria-hidden="true" />
        <div className="relative space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 rounded-full bg-black/10 px-4 py-1 text-xs font-semibold uppercase tracking-widest text-black/70">
                Strategic project dossier
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="text-4xl font-semibold tracking-tight text-black">{project.nom}</h1>
                <Badge variant={isArchived ? 'secondary' : 'default'}>{isArchived ? 'Archived' : 'Active'}</Badge>
              </div>
              <p className="max-w-2xl text-base text-black/70">
                Monitor each stage of this mandate, from briefing to matching insights. Align stakeholders, govern deliverables and keep your recruiting squad focused.
              </p>
            </div>
            <div className="flex flex-col items-end gap-3">
              <Button
                variant="outline"
                className="border-black/30 bg-black/10 text-black hover:bg-black/20"
                onClick={() => (project.enterprise_id ? navigate(`/enterprises/${project.enterprise_id}`) : navigate('/projects'))}
              >
                <ArrowLeft className="mr-2 h-4 w-4" />Back
              </Button>
              
            </div>
          </div>

          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl border border-black/10 bg-black/5 p-5">
              <div className="flex items-center gap-3 text-sm text-black/60">
                <Building2 className="h-4 w-4" />
                Company
              </div>
              <p className="mt-3 text-xl font-semibold text-black">
                {project.enterprise_id ? enterprises.find((e) => e.id === project.enterprise_id)?.nom || project.enterprise_id : '—'}
              </p>
            </div>
            <div className="rounded-2xl border border-black/10 bg-black/5 p-5">
              <div className="flex items-center gap-3 text-sm text-black/60">
                <UserCircle className="h-4 w-4" />
                Hiring manager
              </div>
              <p className="mt-3 text-xl font-semibold text-black">{project.responsable_offre || 'Not specified'}</p>
              <p className="text-sm text-black/60">{project.contact_responsable || 'No contact provided'}</p>
            </div>
            <div className="rounded-2xl border border-black/10 bg-black/5 p-5">
              <div className="flex items-center gap-3 text-sm text-black/60">
                <Briefcase className="h-4 w-4" />
                Department
              </div>
              <p className="mt-3 text-xl font-semibold text-black">
                {project.service_demandeur?.trim() || 'Not specified'}
              </p>
            </div>
            <div className="rounded-2xl border border-black/10 bg-black/5 p-5">
              <div className="flex items-center gap-3 text-sm text-black/60">
                <ShieldCheck className="h-4 w-4" />
                Status overview
              </div>
              <p className="mt-3 text-xl font-semibold text-black">{offerReady ? 'Offer ready' : 'Offer pending'}</p>
              <p className="text-sm text-black/60">{cvsReady ? 'Resumes parsed' : 'Resumes missing'}</p>
            </div>
          </div>
        </div>
      </div>

      {error && <ErrorBanner error={error} />}

      <div className="grid gap-8 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="flex h-full flex-col border border-white/5 bg-white/[0.04]">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Job offer</CardTitle>
                  <CardDescription>
                    {offerReady
                      ? `${offre?.must_have?.length || 0} must-have, ${offre?.nice_have?.length || 0} nice-have`
                      : 'Create the offer for this position'}
                  </CardDescription>
                </div>
                <Badge variant={offerReady ? 'default' : 'secondary'}>{offerReady ? 'Ready' : 'To create'}</Badge>
              </div>
            </CardHeader>
            <CardContent className="flex flex-1 flex-col justify-between gap-6">
              <div className="space-y-3">
                <p className="text-sm text-white/70">
                  Capture a detailed narrative of the mandate, articulate business stakes and document every stakeholder requirement to frame the recruitment brief.
                </p>
                <p className="text-sm text-white/60">
                  Activate AI-driven enrichment to expand the offer with structured responsibilities, value proposition and expected outcomes tailored to the enterprise context.
                </p>
              </div>
              <Button
                className="w-full"
                variant={offerReady ? 'outline' : 'default'}
                onClick={() => navigate(`/projects/${projectId}/offre`)}
              >
                {offerReady ? 'Edit offer' : 'Create offer'}
              </Button>
            </CardContent>
          </Card>

          <Card className="flex h-full flex-col border border-white/5 bg-white/[0.04]">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>CV pipeline</CardTitle>
                  <CardDescription>
                    {cvsReady
                      ? `${cvs.length} parsed CV(s) ready for matching`
                      : 'Upload and parse resumes'}
                  </CardDescription>
                </div>
                <Badge variant={cvsReady ? 'default' : 'secondary'}>{cvsReady ? 'Ready' : 'To prepare'}</Badge>
              </div>
            </CardHeader>
            <CardContent className="flex flex-1 flex-col justify-between gap-6">
              <div className="space-y-3">
                <p className="text-sm text-white/70">
                  Consolidate every profile sourced for this demand, qualify the seniority mix and track coverage versus the hiring objectives.
                </p>
                <p className="text-sm text-white/60">
                  Use AI scoring and parsing insights to surface the most relevant resumes and accelerate shortlisting conversations with business leaders.
                </p>
              </div>
              <Button
                className="w-full"
                variant={cvsReady ? 'outline' : 'default'}
                onClick={() => navigate(`/projects/${projectId}/cvs`)}
              >
                {cvsReady ? 'Manage resumes' : 'Add resumes'}
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="rounded-3xl border border-white/5 bg-white/5 p-8 backdrop-blur-sm">
          <div className="flex items-center gap-3 text-sm font-medium uppercase tracking-widest text-white/50">
            <CheckCircle2 className="h-4 w-4" />
            Readiness checklist
          </div>
          <div className="mt-6 space-y-4">
            <div className="flex items-start gap-3">
              <div className={`mt-1 h-3 w-3 rounded-full ${offerReady ? 'bg-green-400' : 'bg-yellow-400'}`} />
              <div>
                <p className="text-sm font-semibold text-white/85">Offer structured</p>
                <p className="text-sm text-white/60">{offerReady ? 'Offer saved and ready to edit.' : 'Add key details, must-have and nice-to-have criteria.'}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className={`mt-1 h-3 w-3 rounded-full ${cvsReady ? 'bg-green-400' : 'bg-yellow-400'}`} />
              <div>
                <p className="text-sm font-semibold text-white/85">CV pipeline</p>
                <p className="text-sm text-white/60">{cvsReady ? `${cvs.length} resume(s) parsed and ready.` : 'Upload and parse resumes to unlock matching.'}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className={`mt-1 h-3 w-3 rounded-full ${canLaunchMatching ? 'bg-green-400' : 'bg-red-400'}`} />
              <div>
                <p className="text-sm font-semibold text-white/85">Matching readiness</p>
                <p className="text-sm text-white/60">{canLaunchMatching ? 'All prerequisites are satisfied. You can launch matching.' : 'Complete the missing steps above to launch matching.'}</p>
              </div>
            </div>
          </div>
          <div className="mt-8 flex flex-col gap-3">
            <Button
              size="lg"
              className="bg-white text-black hover:bg-white/90"
              disabled={!canLaunchMatching}
              onClick={() => navigate(`/projects/${projectId}/matching`)}
            >
              Launch matching
            </Button>
            <Button
              variant="outline"
              size="lg"
              className="border-white/40 bg-white/10 text-white hover:bg-white/15"
              onClick={() => navigate(`/projects/${projectId}/results`)}
            >
              View latest results
            </Button>
          </div>
        </div>
      </div>

    </div>
  );
};
