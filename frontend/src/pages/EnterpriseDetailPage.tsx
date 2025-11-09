import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Plus,
  FolderOpen,
  Archive,
  Save,
  X,
  Building2,
  Mail,
  Phone,
  Globe,
  Edit,
  Target,
  Calendar,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select } from '../components/ui/select';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '../components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { LoadingPage } from '../components/shared/Loading';
import { ErrorBanner } from '../components/shared/ErrorBanner';
import { EmptyState } from '../components/shared/EmptyState';
import { enterprisesApi } from '../api/enterprises';
import { projectsApi } from '../api/projects';
import type { Enterprise, Project, APIError, Contact } from '../api/types';
import { useToast } from '../hooks/useToast';

export const EnterpriseDetailPage: React.FC = () => {
  const { enterpriseId } = useParams<{ enterpriseId: string }>();
  const navigate = useNavigate();
  const { success, error: showError } = useToast();

  const [enterprise, setEnterprise] = useState<Enterprise | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<APIError | null>(null);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  // Form state for editing the company
  const [formData, setFormData] = useState({
    nom: '',
    site_web: '',
    secteur: '',
    notes: '',
    contacts: [] as Contact[]
  });

  // State for creating a project
  const [projectDialogOpen, setProjectDialogOpen] = useState(false);
  const [projectFormData, setProjectFormData] = useState({
    nom: '',
    enterprise_id: enterpriseId || '',
    service_demandeur: '',
    responsable_offre: '',
    contact_responsable: '',
    notes: ''
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchData = useCallback(async () => {
    if (!enterpriseId) {
      console.warn('[EnterpriseDetailPage] No enterpriseId provided');
      return;
    }

    try {
      console.log('[EnterpriseDetailPage] Loading data for:', enterpriseId);
      setLoading(true);
      setError(null);

      // Load the company and its projects in parallel
      console.log('[EnterpriseDetailPage] Calling API...');
      const [enterpriseData, projectsData] = await Promise.all([
        enterprisesApi.getById(enterpriseId),
        projectsApi.getAll(enterpriseId),
      ]);

      console.log('[EnterpriseDetailPage] Enterprise loaded:', enterpriseData);
      console.log('[EnterpriseDetailPage] Projects loaded:', projectsData.length, 'projects');

      console.log('[EnterpriseDetailPage] About to update state...');
      
      try {
        setEnterprise(enterpriseData);
        console.log('[EnterpriseDetailPage] ✓ Enterprise state set');
        
        const newFormData = {
          nom: enterpriseData.nom,
          site_web: enterpriseData.site_web || '',
          secteur: enterpriseData.secteur || '',
          notes: enterpriseData.notes || '',
          contacts: Array.isArray(enterpriseData.contacts) ? enterpriseData.contacts : []
        };
        console.log('[EnterpriseDetailPage] FormData to set:', newFormData);
        setFormData(newFormData);
        console.log('[EnterpriseDetailPage] ✓ FormData state set');
        
        setProjects(projectsData);
        console.log('[EnterpriseDetailPage] ✓ Projects state set');
        
        console.log('[EnterpriseDetailPage] State updated successfully');
      } catch (err) {
        console.error('[EnterpriseDetailPage] ERROR during state update:', err);
        throw err;
      }
      
      console.log('[EnterpriseDetailPage] Setting loading to false');
      setLoading(false);
      console.log('[EnterpriseDetailPage] ✓ Loading set to false');
    } catch (error: unknown) {
      console.error('[EnterpriseDetailPage] Error loading data:', error);
      console.error('[EnterpriseDetailPage] Error details:', JSON.stringify(error, null, 2));
      
      const errorMessage = error && typeof error === 'object' && 'message' in error 
        ? String(error.message) 
        : 'Unable to load data';
      
      setError({
        code: 'ENTERPRISE_LOAD_ERROR',
        message: errorMessage,
        details: error,
      });
      showError('Error', errorMessage);
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enterpriseId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSave = async () => {
    if (!enterprise) return;

    try {
      setSaving(true);
      await enterprisesApi.update(enterprise.id, formData);
      success('Changes saved');
      setEditing(false);
      // Reload data
      await fetchData();
    } catch (error: unknown) {
      console.error('Unable to save enterprise:', error);
      showError('Error', 'Unable to save changes');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    if (!enterprise) return;
    // Restore original data
    setFormData({
      nom: enterprise.nom,
      site_web: enterprise.site_web || '',
      secteur: enterprise.secteur || '',
      notes: enterprise.notes || '',
      contacts: enterprise.contacts || []
    });
    setEditing(false);
  };

  const addContact = () => {
    setFormData({
      ...formData,
      contacts: [
        ...formData.contacts,
        {
          nom_complet: '',
          email: '',
          poste: '',
          telephone: '',
          canal_prefere: 'email',
          notes: ''
        }
      ]
    });
  };

  const removeContact = (index: number) => {
    setFormData({
      ...formData,
      contacts: formData.contacts.filter((_, i) => i !== index)
    });
  };

  const updateContact = (index: number, field: keyof Contact, value: string) => {
    const updatedContacts = [...formData.contacts];
    updatedContacts[index] = {
      ...updatedContacts[index],
      [field]: value
    };
    setFormData({
      ...formData,
      contacts: updatedContacts
    });
  };

  const handleCreateProject = () => {
    // Open the modal with the enterprise_id prefilled
    setProjectFormData({
      nom: '',
      enterprise_id: enterpriseId || '',
      service_demandeur: '',
      responsable_offre: '',
      contact_responsable: '',
      notes: ''
    });
    setProjectDialogOpen(true);
  };

  const handleCloseProjectDialog = () => {
    setProjectDialogOpen(false);
    setProjectFormData({
      nom: '',
      enterprise_id: enterpriseId || '',
      service_demandeur: '',
      responsable_offre: '',
      contact_responsable: '',
      notes: ''
    });
  };

  const handleSubmitProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!enterpriseId) return;

    setSubmitting(true);
    try {
      // Create the project via the API with enterprise_id
      await projectsApi.create({
        ...projectFormData,
        enterprise_id: enterpriseId
      });
      success('Project created successfully');
      handleCloseProjectDialog();
      // Reload data to display the new project
      await fetchData();
    } catch (error: unknown) {
      console.error('Error creating project:', error);
      showError('Error', 'Unable to create project');
    } finally {
      setSubmitting(false);
    }
  };

  const handleOpenProject = (projectId: string) => {
    navigate(`/projects/${projectId}`);
  };

  const handleArchiveProject = async (projectId: string) => {
    try {
      await projectsApi.delete(projectId);
      success('Project archived');
      await fetchData();
    } catch (error: unknown) {
      console.error('Unable to archive project:', error);
      showError('Error', 'Unable to archive project');
    }
  };

  console.log('[EnterpriseDetailPage] Render - loading:', loading, 'enterprise:', enterprise?.nom, 'projects:', projects.length);
  console.log('[EnterpriseDetailPage] loading type:', typeof loading, 'value:', JSON.stringify(loading));

  if (loading) {
    console.log('[EnterpriseDetailPage] Showing loading page (loading is truthy)');
    return <LoadingPage text="Loading company..." />;
  }
  
  console.log('[EnterpriseDetailPage] Passed loading check');
  
  if (!enterprise) {
    console.log('[EnterpriseDetailPage] No enterprise data, showing not found');
    return <div>Company not found</div>;
  }

  console.log('[EnterpriseDetailPage] Rendering main content');

  const totalProjects = projects.length;
  const activeProjects = projects.filter((p) => p.status === 'actif').length;
  const archivedProjects = projects.filter((p) => p.status === 'archive').length;
  const activeProjectList = projects.filter((p) => p.status === 'actif');
  const archivedProjectList = projects.filter((p) => p.status === 'archive');

  const handleRestoreProject = async (project: Project) => {
    try {
      await projectsApi.update(project.id, {
        nom: project.nom,
        description: project.description || '',
        enterprise_id: project.enterprise_id || enterpriseId || '',
        service_demandeur: project.service_demandeur || '',
        responsable_offre: project.responsable_offre || '',
        contact_responsable: project.contact_responsable || '',
        notes: project.notes || '',
        status: 'actif',
      });
      success('Project restored');
      await fetchData();
    } catch (error: unknown) {
      console.error('Unable to restore project:', error);
      showError('Error', 'Unable to restore project');
    }
  };

  return (
    <div className="space-y-10 rounded-3xl bg-[#0c0c12] p-10 text-gray-100 shadow-[0_45px_140px_-90px_rgba(90,80,255,0.7)]">
      <div className="grid gap-8 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#7f9bff] via-[#8ae1ff] to-[#5df5cb] p-10 text-black shadow-[0px_20px_60px_-30px_rgba(90,140,255,0.7)]">
          <span className="absolute -top-28 -right-16 h-56 w-56 rounded-full bg-white/30 blur-3xl" aria-hidden="true" />
          <span className="absolute bottom-[-70px] left-[-70px] h-72 w-72 rounded-full bg-white/20 blur-3xl" aria-hidden="true" />
          <div className="relative space-y-6">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-3">
                <div className="inline-flex items-center gap-2 rounded-full bg-black/10 px-4 py-1 text-xs font-semibold uppercase tracking-widest text-black/70">
                  Enterprise dossier
                </div>
                <h1 className="text-4xl font-semibold tracking-tight text-black">{enterprise.nom}</h1>
                <p className="max-w-xl text-base text-black/70">
                  Centralize governance artefacts, client history and recruiting pipelines for this enterprise. Launch new mandates instantly and monitor all project streams.
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  className="border-black/30 bg-black/10 text-black hover:bg-black/20"
                  onClick={() => navigate('/enterprises')}
                  aria-label="Back to companies"
                >
                  <ArrowLeft className="mr-2 h-4 w-4" />Back
                </Button>
                <Button onClick={handleCreateProject} className="bg-black text-white hover:bg-black/80">
                  New project
                </Button>
              </div>
            </div>
            <div className="grid gap-5 sm:grid-cols-3">
              <div className="rounded-2xl border border-black/10 bg-black/5 p-5">
                <div className="flex items-center gap-3 text-sm text-black/60">
                  <FolderOpen className="h-4 w-4" />
                  Total projects
                </div>
                <p className="mt-3 text-2xl font-semibold text-black">{totalProjects}</p>
              </div>
              <div className="rounded-2xl border border-black/10 bg-black/5 p-5">
                <div className="flex items-center gap-3 text-sm text-black/60">
                  <Target className="h-4 w-4" />
                  Active mandates
                </div>
                <p className="mt-3 text-2xl font-semibold text-black">{activeProjects}</p>
              </div>
              <div className="rounded-2xl border border-black/10 bg-black/5 p-5">
                <div className="flex items-center gap-3 text-sm text-black/60">
                  <Archive className="h-4 w-4" />
                  Archived
                </div>
                <p className="mt-3 text-2xl font-semibold text-black">{archivedProjects}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-3xl border border-white/5 bg-white/5 p-8 backdrop-blur-sm">
          <div className="flex items-center gap-3 text-sm font-medium uppercase tracking-widest text-white/50">
            <Calendar className="h-4 w-4" />
            Latest activity
          </div>
          <div className="mt-6 space-y-3 text-sm text-white/65">
            <p>• Portfolio created on {enterprise.created_at ? new Date(enterprise.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—'}.</p>
            <p>• {activeProjects} active project(s) in delivery, {archivedProjects} archived pipeline(s).</p>
            <p>• Governance ready: contacts, notes and project history consolidated for executive review.</p>
          </div>
          <div className="mt-8 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/60">
            Need to escalate or share with leadership? Export dossiers and provide explainable matching insights directly from this workspace.
          </div>
        </div>
      </div>

      {error && <ErrorBanner error={error} />}

      <Tabs defaultValue="dashboard" className="space-y-6">
        <TabsList>
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="archived">Archived projects</TabsTrigger>
          <TabsTrigger value="fiche">Company profile</TabsTrigger>
        </TabsList>

        {/* Onglet Tableau de bord */}
        <TabsContent value="dashboard" className="space-y-6">
          <div>
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-semibold text-white">Recruiting projects</h2>
                <p className="text-sm text-white/60">Curated view of every hiring initiative linked to this enterprise.</p>
              </div>
              <Button variant="outline" className="border-white/40 bg-white/10 text-white hover:bg-white/15" onClick={handleCreateProject}>
                <Plus className="mr-2 h-4 w-4" />Add project
              </Button>
            </div>

            {activeProjectList.length === 0 ? (
              <EmptyState
                icon={FolderOpen}
                title="No projects yet"
                description="Create your first recruiting project for this company"
                action={{
                  label: 'Create a project',
                  onClick: handleCreateProject,
                }}
              />
            ) : (
              <div className="mt-5 grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
                {activeProjectList.map((project) => (
                  <Card
                    key={project.id}
                    className="relative overflow-hidden border border-white/5 bg-white/[0.04] transition duration-200 hover:bg-white/[0.08]"
                    onClick={() => handleOpenProject(project.id)}
                  >
                    <span className="absolute inset-0 rounded-3xl bg-gradient-to-br from-white/10 via-transparent to-white/5 opacity-0 transition group-hover:opacity-100" aria-hidden="true" />
                    <CardHeader className="relative">
                      <div className="flex items-start justify-between">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white">
                          <FolderOpen className="h-5 w-5" />
                        </div>
                        <Badge variant={project.status === 'actif' ? 'default' : 'secondary'}>
                          {project.status === 'actif' ? 'Active' : 'Archived'}
                        </Badge>
                      </div>
                      <CardTitle className="mt-4 text-lg text-white">{project.nom}</CardTitle>
                      <CardDescription className="text-white/60">
                        Created on {new Date(project.created_at || '').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </CardDescription>
                    </CardHeader>
                    <CardFooter className="relative flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-white/80 hover:text-white"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/projects/${project.id}`);
                        }}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      {project.status === 'actif' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-white/80 hover:text-white"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleArchiveProject(project.id);
                          }}
                        >
                          <Archive className="h-4 w-4" />
                        </Button>
                      )}
                    </CardFooter>
                  </Card>
                ))}
              </div>
            )}
          </div>

        </TabsContent>

        <TabsContent value="archived" className="space-y-6">
          {archivedProjectList.length === 0 ? (
            <EmptyState
              icon={Archive}
              title="No archived projects"
              description="Archived engagements will appear here for audit and reactivation."
            />
          ) : (
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-semibold text-white">Archived projects</h3>
                <p className="text-sm text-white/55">Historical engagements kept for audit and reporting purposes.</p>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {archivedProjectList.map((project) => (
                  <Card
                    key={project.id}
                    className="relative overflow-hidden border border-white/10 bg-white/[0.03] transition duration-200 hover:bg-white/[0.06]"
                    onClick={() => handleOpenProject(project.id)}
                  >
                    <span className="absolute inset-0 rounded-3xl bg-gradient-to-br from-white/5 via-transparent to-white/10 opacity-0 transition group-hover:opacity-100" aria-hidden="true" />
                    <CardHeader className="relative">
                      <div className="flex items-start justify-between">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white">
                          <FolderOpen className="h-5 w-5" />
                        </div>
                        <Badge variant="secondary">Archived</Badge>
                      </div>
                      <CardTitle className="mt-4 text-lg text-white">{project.nom}</CardTitle>
                      <CardDescription className="text-white/60">
                        Completed on {new Date(project.updated_at || project.created_at || '').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </CardDescription>
                    </CardHeader>
                    <CardFooter className="relative flex justify-end">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-white/70 hover:text-white"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRestoreProject(project);
                        }}
                      >
                        Restore
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-white/70 hover:text-white"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/projects/${project.id}`);
                        }}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </TabsContent>

        {/* Onglet Fiche entreprise */}
        <TabsContent value="fiche" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Company information</CardTitle>
                  <CardDescription>Details and contact information</CardDescription>
                </div>
                {!editing ? (
                  <Button onClick={() => setEditing(true)}>Edit</Button>
                ) : (
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={handleCancel} disabled={saving}>
                      <X className="mr-2 h-4 w-4" />
                      Cancel
                    </Button>
                    <Button onClick={handleSave} disabled={saving}>
                      <Save className="mr-2 h-4 w-4" />
                      {saving ? 'Saving...' : 'Save'}
                    </Button>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Basic information */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                  <Building2 className="h-4 w-4" />
                  General information
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="nom">Name *</Label>
                    {editing ? (
                      <Input
                        id="nom"
                        value={formData.nom}
                        onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
                        placeholder="E.g. TechCorp"
                        required
                      />
                    ) : (
                      <p className="text-base font-medium">{enterprise.nom}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="secteur">Industry</Label>
                    {editing ? (
                      <Input
                        id="secteur"
                        value={formData.secteur}
                        onChange={(e) => setFormData({ ...formData, secteur: e.target.value })}
                        placeholder="E.g. Technology, Finance, Healthcare..."
                      />
                    ) : (
                      <p className="text-base">{enterprise.secteur || '-'}</p>
                    )}
                  </div>
                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="site_web" className="flex items-center gap-2">
                      <Globe className="h-4 w-4" />
                      Website
                    </Label>
                    {editing ? (
                      <Input
                        id="site_web"
                        type="url"
                        value={formData.site_web}
                        onChange={(e) => setFormData({ ...formData, site_web: e.target.value })}
                        placeholder="https://www.example.com"
                      />
                    ) : (
                      enterprise.site_web ? (
                        <a href={enterprise.site_web} target="_blank" rel="noopener noreferrer" className="text-base text-primary hover:underline">
                          {enterprise.site_web}
                        </a>
                      ) : (
                        <p className="text-base text-muted-foreground">-</p>
                      )
                    )}
                  </div>
                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="notes">Notes</Label>
                    {editing ? (
                      <Textarea
                        id="notes"
                        value={formData.notes}
                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                        placeholder="Internal notes about the company..."
                        rows={3}
                      />
                    ) : (
                      <p className="text-base whitespace-pre-wrap">{enterprise.notes || '-'}</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Contacts */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                    <Mail className="h-4 w-4" />
                    Contacts
                  </h3>
                  {editing && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={addContact}
                    >
                      <Plus className="mr-2 h-4 w-4" />
                      Add contact
                    </Button>
                  )}
                </div>

                {formData.contacts.length === 0 ? (
                  <p className="text-base text-muted-foreground">No contacts</p>
                ) : (
                  <div className="space-y-4">
                    {formData.contacts.map((contact, index) => (
                      <Card key={index} className="bg-muted/20">
                        <CardContent className="pt-6">
                          {editing && (
                            <div className="flex justify-end mb-2">
                              <Button
                                type="button"
                                variant="ghost"
                                size="icon"
                                onClick={() => removeContact(index)}
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            </div>
                          )}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <div className="space-y-2">
                              <Label>Full name</Label>
                              {editing ? (
                                <Input
                                  value={contact.nom_complet}
                                  onChange={(e) => updateContact(index, 'nom_complet', e.target.value)}
                                  placeholder="John Doe"
                                  required
                                />
                              ) : (
                                <p className="text-base font-medium">{contact.nom_complet}</p>
                              )}
                            </div>
                            <div className="space-y-2">
                              <Label>Job title</Label>
                              {editing ? (
                                <Input
                                  value={contact.poste || ''}
                                  onChange={(e) => updateContact(index, 'poste', e.target.value)}
                                  placeholder="E.g. HR Manager"
                                />
                              ) : (
                                <p className="text-base">{contact.poste || '-'}</p>
                              )}
                            </div>
                            <div className="space-y-2">
                              <Label className="flex items-center gap-2">
                                <Mail className="h-3 w-3" />
                                Email
                              </Label>
                              {editing ? (
                                <Input
                                  type="email"
                                  value={contact.email}
                                  onChange={(e) => updateContact(index, 'email', e.target.value)}
                                  placeholder="john.doe@example.com"
                                />
                              ) : (
                                <a href={`mailto:${contact.email}`} className="text-base text-primary hover:underline">
                                  {contact.email}
                                </a>
                              )}
                            </div>
                            <div className="space-y-2">
                              <Label className="flex items-center gap-2">
                                <Phone className="h-3 w-3" />
                                Phone
                              </Label>
                              {editing ? (
                                <Input
                                  type="tel"
                                  value={contact.telephone || ''}
                                  onChange={(e) => updateContact(index, 'telephone', e.target.value)}
                                  placeholder="+1 555 123 4567"
                                />
                              ) : (
                                <p className="text-base">{contact.telephone || '-'}</p>
                              )}
                            </div>
                            <div className="space-y-2">
                              <Label>Preferred channel</Label>
                              {editing ? (
                                <Select
                                  value={contact.canal_prefere || 'email'}
                                  onChange={(e) => updateContact(index, 'canal_prefere', e.target.value)}
                                >
                                  <option value="email">Email</option>
                                  <option value="telephone">Phone</option>
                                  <option value="slack">Slack</option>
                                  <option value="autre">Other</option>
                                </Select>
                              ) : (
                                <p className="text-base capitalize">{contact.canal_prefere || 'email'}</p>
                              )}
                            </div>
                            {(editing || contact.notes) && (
                              <div className="space-y-2 md:col-span-2">
                                <Label>Notes</Label>
                                {editing ? (
                                  <Textarea
                                    value={contact.notes || ''}
                                    onChange={(e) => updateContact(index, 'notes', e.target.value)}
                                  placeholder="Additional information..."
                                    rows={2}
                                  />
                                ) : (
                                  <p className="text-base whitespace-pre-wrap">{contact.notes}</p>
                                )}
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Project creation dialog */}
      <Dialog open={projectDialogOpen} onOpenChange={setProjectDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <form onSubmit={handleSubmitProject}>
            <DialogHeader>
              <DialogTitle>New project</DialogTitle>
            </DialogHeader>
            <div className="space-y-6 py-4">
              {/* Basic information */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-foreground">Basic information</h3>
                <div className="space-y-2">
                  <Label htmlFor="project-nom">Project name *</Label>
                  <Input
                    id="project-nom"
                    value={projectFormData.nom}
                    onChange={(e) => setProjectFormData({ ...projectFormData, nom: e.target.value })}
                    placeholder="E.g. Senior Developer recruitment"
                    required
                    disabled={submitting}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="project-service">Requesting department</Label>
                  <Input
                    id="project-service"
                    value={projectFormData.service_demandeur}
                    onChange={(e) => setProjectFormData({ ...projectFormData, service_demandeur: e.target.value })}
                    placeholder="E.g. IT, HR, Marketing..."
                    disabled={submitting}
                  />
                </div>
              </div>

              {/* Contact and follow-up */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-foreground">Contact and follow-up</h3>
                <div className="space-y-2">
                  <Label htmlFor="project-responsable">Hiring manager</Label>
                  <Input
                    id="project-responsable"
                    value={projectFormData.responsable_offre}
                    onChange={(e) => setProjectFormData({ ...projectFormData, responsable_offre: e.target.value })}
                    placeholder="E.g. Mary Smith"
                    disabled={submitting}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="project-contact">Point of contact</Label>
                  <Input
                    id="project-contact"
                    type="email"
                    value={projectFormData.contact_responsable}
                    onChange={(e) => setProjectFormData({ ...projectFormData, contact_responsable: e.target.value })}
                    placeholder="E.g. mary.smith@company.com"
                    disabled={submitting}
                  />
                </div>
              </div>

              {/* Notes */}
              <div className="space-y-2">
                <Label htmlFor="project-notes">Internal notes</Label>
                <Textarea
                  id="project-notes"
                  value={projectFormData.notes}
                  onChange={(e) => setProjectFormData({ ...projectFormData, notes: e.target.value })}
                  placeholder="Additional notes and context..."
                  rows={3}
                  disabled={submitting}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleCloseProjectDialog} disabled={submitting}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? 'Creating...' : 'Create project'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};
