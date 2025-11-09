import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Pencil, Trash2, History, FolderOpen, ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogClose,
} from '../components/ui/dialog';
import { Card, CardTitle } from '../components/ui/card';
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
import { enterprisesApi } from '../api/enterprises';
import type { Project, Enterprise, APIError, ProjectHistory } from '../api/types';

export const ProjectsPage: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [enterprises, setEnterprises] = useState<Enterprise[]>([]);
  const [selectedEnterpriseId, setSelectedEnterpriseId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<APIError | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [projectHistory, setProjectHistory] = useState<ProjectHistory | null>(null);
  const [formData, setFormData] = useState({
    nom: '',
    enterprise_id: '',
    service_demandeur: '',
    responsable_offre: '',
    contact_responsable: '',
    notes: ''
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchEnterprises = async () => {
    try {
      const data = await enterprisesApi.getAll();
      setEnterprises(data);
    } catch (err) {
      console.error('Failed to fetch enterprises:', err);
    }
  };

  const fetchProjects = async (enterpriseId?: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await projectsApi.getAll(enterpriseId);
      setProjects(data);
    } catch (err) {
      setError(err as APIError);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEnterprises();
    fetchProjects();
  }, []);

  useEffect(() => {
    fetchProjects(selectedEnterpriseId || undefined);
  }, [selectedEnterpriseId]);

  const handleOpenDialog = (project?: Project) => {
    if (project) {
      setEditingProject(project);
      setFormData({
        nom: project.nom,
        enterprise_id: project.enterprise_id || '',
        service_demandeur: project.service_demandeur || '',
        responsable_offre: project.responsable_offre || '',
        contact_responsable: project.contact_responsable || '',
        notes: project.notes || ''
      });
    } else {
      setEditingProject(null);
      setFormData({
        nom: '',
        enterprise_id: selectedEnterpriseId,
        service_demandeur: '',
        responsable_offre: '',
        contact_responsable: '',
        notes: ''
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingProject(null);
    setFormData({
      nom: '',
      enterprise_id: '',
      service_demandeur: '',
      responsable_offre: '',
      contact_responsable: '',
      notes: ''
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (editingProject) {
        const updated = await projectsApi.update(editingProject.id, formData);
        console.log('✅ Project updated:', updated);
      } else {
        await projectsApi.create(formData);
      }
      handleCloseDialog();
      // Force refresh
      await fetchProjects(selectedEnterpriseId || undefined);
    } catch (err) {
      console.error('❌ Update error:', err);
      setError(err as APIError);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deletingId) return;
    setSubmitting(true);
    try {
      await projectsApi.delete(deletingId);
      await fetchProjects(selectedEnterpriseId || undefined);
      setDeleteDialogOpen(false);
      setDeletingId(null);
    } catch (err) {
      setError(err as APIError);
    } finally {
      setSubmitting(false);
    }
  };

  const openDeleteDialog = (id: string) => {
    setDeletingId(id);
    setDeleteDialogOpen(true);
  };

  const openHistoryDialog = async (projectId: string) => {
    try {
      const history = await projectsApi.getHistory(projectId);
      setProjectHistory(history);
      setHistoryDialogOpen(true);
    } catch (err) {
      setError(err as APIError);
    }
  };

  const getEnterpriseName = (enterpriseId?: string) => {
    if (!enterpriseId) return 'Unassigned';
    const enterprise = enterprises.find((e) => e.id === enterpriseId);
    return enterprise?.nom || enterpriseId;
  };

  const formatDate = (value?: string | null) => {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '—';
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const heroGradient = 'from-[#7f8bff] via-[#8ed4ff] to-[#53f4c8]';
  const totalProjects = projects.length;
  const activeProjects = projects.filter((project) => project.status === 'actif').length;
  const archivedProjects = projects.filter((project) => project.status === 'archive').length;
  const lastUpdatedProject = projects.reduce<Date | null>((latest, project) => {
    if (!project.last_modified) return latest;
    const current = new Date(project.last_modified);
    if (Number.isNaN(current.getTime())) return latest;
    if (!latest || current > latest) return current;
    return latest;
  }, null);
  const lastUpdatedLabel = lastUpdatedProject
    ? lastUpdatedProject.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    : '—';
  const heroBadge = selectedEnterpriseId ? getEnterpriseName(selectedEnterpriseId) : 'All companies';

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
                Projects cockpit
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <Badge variant="secondary" className="bg-white/20 text-black">
                {heroBadge}
              </Badge>
              <Button
                size="lg"
                className="bg-black text-white hover:bg-black/80"
                onClick={() => handleOpenDialog()}
              >
                <Plus className="mr-2 h-4 w-4" />
                New project
              </Button>
            </div>
          </div>
          <div className="space-y-4">
            <h1 className="text-4xl font-semibold tracking-tight text-black">Project portfolio oversight</h1>
            <p className="max-w-2xl text-base text-black/70">
              Orchestrate active mandates, monitor archived missions and align recruitment squads in one corporate workspace.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl border border-black/10 bg-black/5 p-4">
              <p className="text-xs uppercase tracking-widest text-black/50">Total projects</p>
              <p className="mt-2 text-lg font-semibold text-black">{totalProjects}</p>
            </div>
            <div className="rounded-2xl border border-black/10 bg-black/5 p-4">
              <p className="text-xs uppercase tracking-widest text-black/50">Active</p>
              <p className="mt-2 text-lg font-semibold text-black">{activeProjects}</p>
            </div>
            <div className="rounded-2xl border border-black/10 bg-black/5 p-4">
              <p className="text-xs uppercase tracking-widest text-black/50">Archived</p>
              <p className="mt-2 text-lg font-semibold text-black">{archivedProjects}</p>
            </div>
            <div className="rounded-2xl border border-black/10 bg-black/5 p-4">
              <p className="text-xs uppercase tracking-widest text-black/50">Last update</p>
              <p className="mt-2 text-lg font-semibold text-black">{lastUpdatedLabel}</p>
            </div>
          </div>
        </div>
      </div>

      {error && <ErrorBanner error={error} />}

      <div className="flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-white/5 bg-white/[0.04] p-6">
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-widest text-white/50">Filter scope</p>
          <p className="text-sm text-white/60">Focus on one company to tighten the recruitment view.</p>
        </div>
        <div className="w-full min-w-[220px] max-w-xs">
          <Label htmlFor="enterprise-filter" className="sr-only">
            Filter by company
          </Label>
          <Select
            id="enterprise-filter"
            value={selectedEnterpriseId}
            onChange={(e) => setSelectedEnterpriseId(e.target.value)}
            className="border-white/20 bg-white text-slate-900 focus:border-white/40"
          >
            <option value="">All companies</option>
            {enterprises.map((enterprise) => (
              <option key={enterprise.id} value={enterprise.id}>
                {enterprise.nom}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {projects.length === 0 ? (
        <div className="rounded-3xl border border-white/5 bg-white/[0.03] p-10">
          <EmptyState
            icon={FolderOpen}
            title="No projects yet"
            description="Create your first recruiting project"
            action={{
              label: 'Create a project',
              onClick: () => handleOpenDialog(),
            }}
          />
        </div>
      ) : (
        <section className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {projects.map((project) => {
            const createdLabel = formatDate(project.created_at);
            const updatedLabel = formatDate(project.last_modified);
            const statusLabel = project.status === 'actif' ? 'Active' : 'Archived';
            const departmentLabel = project.service_demandeur || 'Department not specified';
            const managerLabel = project.responsable_offre || 'Manager not specified';

            return (
              <Card
                key={project.id}
                className="group relative cursor-pointer overflow-hidden rounded-3xl border border-white/5 bg-white/[0.04] p-6 transition-all duration-300 hover:border-white/15 hover:bg-white/[0.07]"
                onClick={() => navigate(`/projects/${project.id}`)}
              >
                <span
                  className="absolute inset-0 rounded-3xl bg-gradient-to-br from-white/10 via-transparent to-white/5 opacity-0 transition-opacity group-hover:opacity-100"
                  aria-hidden="true"
                />
                <div className="relative flex h-full flex-col gap-6">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-2">
                      <CardTitle className="text-xl font-semibold text-white">{project.nom}</CardTitle>
                      <p className="text-sm text-white/60">{getEnterpriseName(project.enterprise_id)}</p>
                    </div>
                    <Badge className={project.status === 'actif' ? 'bg-emerald-400/20 text-emerald-100' : 'bg-white/15 text-white'}>
                      {statusLabel}
                    </Badge>
                  </div>

                  <div className="space-y-3 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/70">
                    <p className="flex items-center justify-between">
                      <span>Created</span>
                      <span>{createdLabel}</span>
                    </p>
                    <p className="flex items-center justify-between">
                      <span>Last update</span>
                      <span>{updatedLabel}</span>
                    </p>
                  </div>

                  <div className="flex items-start justify-between gap-3 pt-2">
                    <div className="space-y-1 text-xs">
                      <p className="uppercase tracking-widest text-white/50">
                        {departmentLabel && departmentLabel.length > 0 ? departmentLabel : 'Department not specified'}
                      </p>
                      {managerLabel && (
                        <p className="text-white/60">
                          Manager:{' '}
                          <span className="font-medium text-white">
                            {managerLabel}
                          </span>
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="rounded-full border border-white/10 bg-white/10 text-white hover:bg-white/20"
                        onClick={(e) => {
                          e.stopPropagation();
                          openHistoryDialog(project.id);
                        }}
                        aria-label="View project history"
                      >
                        <History className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="rounded-full border border-white/10 bg-white/10 text-white hover:bg-white/20"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenDialog(project);
                        }}
                        aria-label="Edit project"
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="rounded-full border border-white/10 bg-white/10 text-white hover:bg-white/20"
                        onClick={(e) => {
                          e.stopPropagation();
                          openDeleteDialog(project.id);
                        }}
                        aria-label="Delete project"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </section>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
          <DialogClose onClick={handleCloseDialog} />
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>
                {editingProject ? 'Edit project' : 'New project'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-6 py-4">
              {/* Informations de base */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-foreground">Basic information</h3>
                <div className="space-y-2">
                  <Label htmlFor="nom">Project name *</Label>
                  <Input
                    id="nom"
                    value={formData.nom}
                    onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
                    placeholder="E.g. Senior Developer recruitment"
                    required
                    disabled={submitting}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="enterprise_id">Company *</Label>
                  <Select
                    id="enterprise_id"
                    value={formData.enterprise_id}
                    onChange={(e) => setFormData({ ...formData, enterprise_id: e.target.value })}
                    disabled={submitting}
                    required
                  >
                    <option value="">Select a company</option>
                    {enterprises.map((enterprise) => (
                      <option key={enterprise.id} value={enterprise.id}>
                        {enterprise.nom}
                      </option>
                    ))}
                  </Select>
                </div>
              </div>

              {/* Additional information */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-foreground">Additional details</h3>
                <div className="space-y-2">
                  <Label htmlFor="service_demandeur">Requesting department</Label>
                  <Input
                    id="service_demandeur"
                    value={formData.service_demandeur}
                    onChange={(e) => setFormData({ ...formData, service_demandeur: e.target.value })}
                    placeholder="E.g. IT department, HR..."
                    disabled={submitting}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="responsable_offre">Hiring manager</Label>
                  <Input
                    id="responsable_offre"
                    value={formData.responsable_offre}
                    onChange={(e) => setFormData({ ...formData, responsable_offre: e.target.value })}
                    placeholder="Manager name"
                    disabled={submitting}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="contact_responsable">Manager contact</Label>
                  <Input
                    id="contact_responsable"
                    value={formData.contact_responsable}
                    onChange={(e) => setFormData({ ...formData, contact_responsable: e.target.value })}
                    placeholder="Email or phone"
                    disabled={submitting}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="notes">Notes</Label>
                  <Textarea
                    id="notes"
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    placeholder="Internal notes about the project..."
                    rows={3}
                    disabled={submitting}
                  />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleCloseDialog} disabled={submitting}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? 'Saving...' : editingProject ? 'Save changes' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent onClick={(e) => e.stopPropagation()}>
          <DialogClose onClick={() => setDeleteDialogOpen(false)} />
          <DialogHeader>
            <DialogTitle>Confirm deletion</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground py-4">
            Are you sure you want to delete this project? This action cannot be undone.
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)} disabled={submitting}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete} disabled={submitting}>
              {submitting ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* History Dialog */}
      <Dialog open={historyDialogOpen} onOpenChange={setHistoryDialogOpen}>
        <DialogContent onClick={(e) => e.stopPropagation()}>
          <DialogClose onClick={() => setHistoryDialogOpen(false)} />
          <DialogHeader>
            <DialogTitle>Project history</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            {projectHistory && projectHistory.total > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Candidates</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {projectHistory.items.map((item) => (
                    <TableRow key={item.matching_id}>
                      <TableCell>
                        {new Date(item.timestamp).toLocaleString('en-US')}
                      </TableCell>
                      <TableCell>{item.candidats_count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">
                No history available
              </p>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
