import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus, Pencil, Trash2, Building2, X, Briefcase, ShieldCheck, Target } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogClose,
} from '../components/ui/dialog';
import { Select } from '../components/ui/select';
import { LoadingPage } from '../components/shared/Loading';
import { ErrorBanner } from '../components/shared/ErrorBanner';
import { EmptyState } from '../components/shared/EmptyState';
import { enterprisesApi } from '../api/enterprises';
import type { Enterprise, Contact, APIError } from '../api/types';

export const EnterprisesPage: React.FC = () => {
  const navigate = useNavigate();
  const [enterprises, setEnterprises] = useState<Enterprise[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<APIError | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingEnterprise, setEditingEnterprise] = useState<Enterprise | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({
    nom: '',
    site_web: '',
    secteur: '',
    notes: '',
    contacts: [] as Contact[],
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchEnterprises = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await enterprisesApi.getAll();
      setEnterprises(data);
    } catch (err) {
      setError(err as APIError);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEnterprises();
  }, []);

  const handleOpenDialog = (enterprise?: Enterprise) => {
    if (enterprise) {
      setEditingEnterprise(enterprise);
      setFormData({
        nom: enterprise.nom,
        site_web: enterprise.site_web || '',
        secteur: enterprise.secteur || '',
        notes: enterprise.notes || '',
        contacts: enterprise.contacts || [],
      });
    } else {
      setEditingEnterprise(null);
      setFormData({
        nom: '',
        site_web: '',
        secteur: '',
        notes: '',
        contacts: [],
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingEnterprise(null);
    setFormData({
      nom: '',
      site_web: '',
      secteur: '',
      notes: '',
      contacts: [],
    });
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
          notes: '',
        },
      ],
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (editingEnterprise) {
        await enterprisesApi.update(editingEnterprise.id, formData);
      } else {
        await enterprisesApi.create(formData);
      }
      await fetchEnterprises();
      handleCloseDialog();
    } catch (err) {
      setError(err as APIError);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deletingId) return;
    setSubmitting(true);
    try {
      await enterprisesApi.delete(deletingId);
      await fetchEnterprises();
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

  if (loading) return <LoadingPage text="Loading companies..." />;

  const totalProjects = enterprises.reduce((acc, enterprise) => acc + (enterprise.projects_count || 0), 0);
  const activeEnterprises = enterprises.length;
  const industries = new Set(enterprises.map((enterprise) => enterprise.secteur).filter(Boolean));
  const normalizedSearch = searchTerm.trim().toLowerCase();
  const filteredEnterprises = enterprises.filter((enterprise) =>
    enterprise.nom.toLowerCase().includes(normalizedSearch)
  );
  const hasSearch = normalizedSearch.length > 0;
  const hasFilteredResults = filteredEnterprises.length > 0;

  return (
    <div className="space-y-10 rounded-3xl bg-[#0c0c12] p-10 text-gray-100 shadow-[0_45px_140px_-90px_rgba(90,80,255,0.7)]">
      <div className="grid gap-8 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#7f8bff] via-[#8ad1ff] to-[#58f3c5] p-10 text-black shadow-[0px_20px_60px_-30px_rgba(90,140,255,0.7)]">
          <span className="absolute -top-28 -right-16 h-56 w-56 rounded-full bg-white/30 blur-3xl" aria-hidden="true" />
          <span className="absolute bottom-[-80px] left-[-70px] h-72 w-72 rounded-full bg-white/25 blur-3xl" aria-hidden="true" />
          <div className="relative space-y-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  size="icon"
                  className="border-black/30 bg-black/10 text-black hover:bg-black/20"
                  onClick={() => navigate('/')}
                  aria-label="Back to dashboard"
                >
                  <ArrowLeft className="h-4 w-4" />
                </Button>
                <div className="inline-flex items-center gap-2 rounded-full bg-black/10 px-4 py-1 text-xs font-semibold uppercase tracking-widest text-black/70">
                  Enterprise landscape
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Button size="lg" onClick={() => handleOpenDialog()} className="bg-black text-white hover:bg-black/80">
                  Add company
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="border-black/30 bg-black/10 text-black hover:bg-black/20"
                  onClick={() => navigate('/projects')}
                >
                  View projects
                </Button>
              </div>
            </div>
            <div className="space-y-3">
              <h1 className="text-4xl font-semibold tracking-tight text-black">Shape your client portfolio with confidence.</h1>
              <p className="max-w-xl text-base text-black/70">
                All your enterprise accounts, governance workflows and internal notes orchestrated in a single, premium workspace. Monitor project pipelines, safeguard compliance and launch new mandates instantly.
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-3xl border border-white/5 bg-white/5 p-8 backdrop-blur-sm">
          <div className="flex items-center gap-3 text-sm font-medium uppercase tracking-widest text-white/50">
            <Building2 className="h-4 w-4" />
            Portfolio snapshot
          </div>
          <div className="mt-8 grid gap-5 sm:grid-cols-3">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
              <div className="flex items-center gap-3 text-sm text-white/60">
                <Briefcase className="h-4 w-4" />
                Active companies
              </div>
              <p className="mt-3 text-2xl font-semibold text-white">{activeEnterprises}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
              <div className="flex items-center gap-3 text-sm text-white/60">
                <Target className="h-4 w-4" />
                Projects pipeline
              </div>
              <p className="mt-3 text-2xl font-semibold text-white">{totalProjects}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
              <div className="flex items-center gap-3 text-sm text-white/60">
                <ShieldCheck className="h-4 w-4" />
                Industries covered
              </div>
              <p className="mt-3 text-2xl font-semibold text-white">{industries.size}</p>
            </div>
          </div>
          <div className="mt-8 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/65">
            Governance-ready records, structured contacts and audit trails designed for corporate HR teams.
          </div>
        </div>
      </div>

      {error && <ErrorBanner error={error} />}

      <div className="flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-white/5 bg-white/[0.04] p-6">
        <div className="w-full flex-1 min-w-[220px] max-w-md">
          <Input
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            placeholder="Search company by name..."
            aria-label="Search companies"
            className="border-white/20 bg-white/[0.08] text-white placeholder:text-white/50"
          />
        </div>
      </div>

      {enterprises.length === 0 ? (
        <EmptyState
          icon={Building2}
          title="No companies yet"
          description="Create your first company to get started"
          action={{
            label: 'Create a company',
            onClick: () => handleOpenDialog(),
          }}
        />
      ) : hasFilteredResults ? (
        <section className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {filteredEnterprises.map((enterprise) => (
            <div
              key={enterprise.id}
              className="group relative overflow-hidden rounded-3xl border border-white/5 bg-white/[0.04] p-6 transition duration-200 hover:bg-white/[0.07]"
              role="button"
              tabIndex={0}
              onClick={() => navigate(`/enterprises/${enterprise.id}`)}
              onKeyPress={(event) => {
                if (event.key === 'Enter' || event.key === ' ') navigate(`/enterprises/${enterprise.id}`);
              }}
            >
              <span className="absolute inset-0 rounded-3xl bg-gradient-to-br from-white/10 via-transparent to-white/5 opacity-0 transition group-hover:opacity-100" aria-hidden="true" />
              <div className="relative space-y-5">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-white">{enterprise.nom}</h2>
                    <p className="text-sm text-white/60">{enterprise.secteur || 'Industry not specified'}</p>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-white/60">
                    <span>{enterprise.projects_count || 0} project(s)</span>
                  </div>
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/65">
                  <p className="flex items-center justify-between">
                    <span>Created on</span>
                    <span>{enterprise.created_at ? new Date(enterprise.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '-'}</span>
                  </p>
                  {enterprise.site_web && (
                    <p className="mt-2 truncate text-xs text-white/50">
                      {enterprise.site_web}
                    </p>
                  )}
                </div>

                <div className="flex justify-end gap-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-white/70 hover:text-white"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleOpenDialog(enterprise);
                    }}
                    aria-label="Edit enterprise"
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-white/70 hover:text-white"
                    onClick={(e) => {
                      e.stopPropagation();
                      openDeleteDialog(enterprise.id);
                    }}
                    aria-label="Delete enterprise"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </section>
      ) : (
        <div className="rounded-3xl border border-white/5 bg-white/[0.03] p-10 text-center text-white/60">
          {hasSearch
            ? 'No company matches your search. Try adjusting the name or clear the filter.'
            : 'No company to display yet.'}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
          <DialogClose onClick={handleCloseDialog} />
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>
                {editingEnterprise ? 'Edit company' : 'New company'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-6 py-4">
              {/* Informations de base */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-foreground">Basic information</h3>
                <div className="space-y-2">
                  <Label htmlFor="nom">Name *</Label>
                  <Input
                    id="nom"
                    value={formData.nom}
                    onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
                    placeholder="E.g. TechCorp"
                    required
                    disabled={submitting}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="site_web">Website</Label>
                  <Input
                    id="site_web"
                    type="url"
                    value={formData.site_web}
                    onChange={(e) => setFormData({ ...formData, site_web: e.target.value })}
                    placeholder="https://www.example.com"
                    disabled={submitting}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="secteur">Industry</Label>
                  <Input
                    id="secteur"
                    value={formData.secteur}
                    onChange={(e) => setFormData({ ...formData, secteur: e.target.value })}
                    placeholder="E.g. Technology, Finance, Healthcare..."
                    disabled={submitting}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="notes">Notes</Label>
                  <Textarea
                    id="notes"
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    placeholder="Internal notes about the company..."
                    rows={3}
                    disabled={submitting}
                  />
                </div>
              </div>

              {/* Contacts */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-foreground">Contacts</h3>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={addContact}
                    disabled={submitting}
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Add contact
                  </Button>
                </div>

                {formData.contacts.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No contacts added</p>
                ) : (
                  <div className="space-y-4">
                    {formData.contacts.map((contact, index) => (
                      <div key={index} className="border rounded-lg p-4 space-y-3 bg-muted/20">
                        <div className="flex items-center justify-between">
                          <h4 className="text-sm font-medium">Contact {index + 1}</h4>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            onClick={() => removeContact(index)}
                            disabled={submitting}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="space-y-2">
                            <Label htmlFor={`contact-nom-${index}`}>Full name *</Label>
                            <Input
                              id={`contact-nom-${index}`}
                              value={contact.nom_complet}
                              onChange={(e) => updateContact(index, 'nom_complet', e.target.value)}
                              placeholder="John Doe"
                              required
                              disabled={submitting}
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor={`contact-poste-${index}`}>Job title</Label>
                            <Input
                              id={`contact-poste-${index}`}
                              value={contact.poste || ''}
                              onChange={(e) => updateContact(index, 'poste', e.target.value)}
                              placeholder="E.g. HR Manager"
                              disabled={submitting}
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor={`contact-email-${index}`}>Email *</Label>
                            <Input
                              id={`contact-email-${index}`}
                              type="email"
                              value={contact.email}
                              onChange={(e) => updateContact(index, 'email', e.target.value)}
                              placeholder="john.doe@example.com"
                              required
                              disabled={submitting}
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor={`contact-telephone-${index}`}>Phone</Label>
                            <Input
                              id={`contact-telephone-${index}`}
                              type="tel"
                              value={contact.telephone || ''}
                              onChange={(e) => updateContact(index, 'telephone', e.target.value)}
                              placeholder="+1 555 123 4567"
                              disabled={submitting}
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor={`contact-canal-${index}`}>Preferred channel</Label>
                            <Select
                              id={`contact-canal-${index}`}
                              value={contact.canal_prefere || 'email'}
                              onChange={(e) => updateContact(index, 'canal_prefere', e.target.value)}
                              disabled={submitting}
                            >
                              <option value="email">Email</option>
                              <option value="telephone">Phone</option>
                              <option value="slack">Slack</option>
                              <option value="autre">Other</option>
                            </Select>
                          </div>
                          <div className="space-y-2 col-span-2">
                            <Label htmlFor={`contact-notes-${index}`}>Notes</Label>
                            <Textarea
                              id={`contact-notes-${index}`}
                              value={contact.notes || ''}
                              onChange={(e) => updateContact(index, 'notes', e.target.value)}
                              placeholder="Additional information..."
                              rows={2}
                              disabled={submitting}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleCloseDialog} disabled={submitting}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? 'Saving...' : editingEnterprise ? 'Save changes' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent onClick={(e) => e.stopPropagation()}>
          <DialogClose onClick={() => setDeleteDialogOpen(false)} />
          <DialogHeader>
            <DialogTitle>Confirm deletion</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground py-4">
            Are you sure you want to delete this company? This action cannot be undone.
          </p>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete} disabled={submitting}>
              {submitting ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
