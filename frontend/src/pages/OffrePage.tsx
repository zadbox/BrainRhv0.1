import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Save, Sparkles, Loader2, CheckCircle, Upload, FileText, Plus, X } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select } from '../components/ui/select';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { LoadingPage } from '../components/shared/Loading';
import { ErrorBanner } from '../components/shared/ErrorBanner';
import { offresApi } from '../api/offres';
import { projectsApi } from '../api/projects';
import type {
  Offre,
  APIError,
  Project,
  EnrichmentResult,
  EnrichmentSelections,
  QuestionResponses,
} from '../api/types';
import { useToast } from '../hooks/useToast';

type CriteriaClassification = 'N/A' | 'Must-have' | 'Nice-to-have';

interface CriteriaItem {
  text: string;
  source: 'ia' | 'manual';
  classification: CriteriaClassification;
}

export const OffrePage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { success, error: showError } = useToast();

  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<APIError | null>(null);

  // === SECTION 1: Préparer l'offre ===
  const [inputMethod, setInputMethod] = useState<'text' | 'file'>('text');
  const [offreText, setOffreText] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [parsing, setParsing] = useState(false);

  // Offre parsée
  const [offreData, setOffreData] = useState<Offre | null>(null);

  // === SECTION 2: Enrichissement ===
  const [enriching, setEnriching] = useState(false);
  const [enrichmentResult, setEnrichmentResult] = useState<EnrichmentResult | null>(null);
  const [selections, setSelections] = useState<EnrichmentSelections>({
    competences: [],
    outils: [],
    langages: [],
    certifications: [],
    missions: [],
  });
  const [questionResponses, setQuestionResponses] = useState<QuestionResponses>({});

  // === SECTION 3: Critères Must-have/Nice-have ===
  const [extractingCriteria, setExtractingCriteria] = useState(false);
  const [criteriaList, setCriteriaList] = useState<CriteriaItem[]>([]);
  const [manualCriteriaText, setManualCriteriaText] = useState('');

  const fetchData = useCallback(async () => {
    if (!projectId) return;

    try {
      setLoading(true);
      setError(null);

      const projectData = await projectsApi.getById(projectId);
      setProject(projectData);

      // Charger offre existante si disponible
      try {
        const existingOffre = await offresApi.getByProject(projectId);
        setOffreData(existingOffre);
      } catch {
        // Pas d'offre existante
      }
    } catch (err) {
      setError(err as APIError);
      showError('Erreur', 'Impossible de charger le projet');
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  useEffect(() => {
    if (!projectId) return;
    fetchData();
  }, [projectId, fetchData]);

  // === HANDLERS SECTION 1 ===
  const handleParseOffre = async () => {
    if (!projectId) return;

    if (inputMethod === 'text' && !offreText.trim()) {
      showError('Erreur', 'Veuillez saisir le texte de l\'offre');
      return;
    }

    if (inputMethod === 'file' && !selectedFile) {
      showError('Erreur', 'Veuillez sélectionner un fichier');
      return;
    }

    setParsing(true);
    try {
      let parsed;

      if (inputMethod === 'text') {
        parsed = await offresApi.parseText(projectId, offreText);
      } else {
        parsed = await offresApi.parseFile(projectId, selectedFile!);
      }

      setOffreData(parsed);
      success('Offre parsée', 'L\'offre a été analysée avec succès');
    } catch (err) {
      setError(err as APIError);
      showError('Erreur', 'Échec du parsing de l\'offre');
    } finally {
      setParsing(false);
    }
  };

  // === HANDLERS SECTION 2 ===
  const handleEnrichWithAI = async () => {
    if (!projectId) {
      showError('Erreur', 'Projet introuvable');
      return;
    }

    // Utiliser description existante OU le texte saisi
    const descriptionToEnrich = offreData?.sections?.description || offreText;

    if (!descriptionToEnrich) {
      showError('Erreur', 'Veuillez d\'abord saisir ou parser une offre');
      return;
    }

    setEnriching(true);
    try {
      const result = await offresApi.enrich(projectId, descriptionToEnrich);
      setEnrichmentResult(result);
      setSelections({
        competences: [],
        outils: [],
        langages: [],
        certifications: [],
        missions: [],
      });
      setQuestionResponses({});
      success('Enrichissement terminé', `Score: ${result.coverage_score}%`);
    } catch (err) {
      setError(err as APIError);
      showError('Erreur', 'Échec de l\'enrichissement IA');
    } finally {
      setEnriching(false);
    }
  };

  const toggleSelection = (category: keyof EnrichmentSelections, index: number) => {
    setSelections((prev) => {
      const current = prev[category];
      const next = current.includes(index)
        ? current.filter((i) => i !== index)
        : [...current, index];
      return {
        ...prev,
        [category]: next,
      };
    });
  };

  const handleApplyEnrichment = async () => {
    if (!projectId || !offreData || !enrichmentResult) return;

    try {
      // Calculer le nombre total d'éléments sélectionnés
      const totalSelected =
        selections.competences.length +
        selections.outils.length +
        selections.langages.length +
        selections.certifications.length +
        selections.missions.length +
        Object.keys(questionResponses).filter((k) => questionResponses[k]?.trim()).length;

      const payload = {
        offre: offreData,
        enrichment: enrichmentResult,
        selections,
        question_responses: questionResponses,
      };

      const enriched = await offresApi.applyEnrichment(projectId, payload as Record<string, unknown>);

      setOffreData(enriched);
      setEnrichmentResult(null);
      success(
        'Enrichissement appliqué',
        `${totalSelected} élément${totalSelected > 1 ? 's' : ''} ajouté${totalSelected > 1 ? 's' : ''} à l'offre`
      );
    } catch (err) {
      setError(err as APIError);
      showError('Erreur', 'Échec de l\'application');
    }
  };

  // === HANDLERS SECTION 3 ===
  const handleExtractCriteria = async () => {
    if (!projectId || !offreText) {
      showError('Erreur', 'Veuillez d\'abord saisir l\'offre');
      return;
    }

    setExtractingCriteria(true);
    try {
      const result = await offresApi.extractCriteria(projectId, offreText);

      const newCriteria: CriteriaItem[] = result.criteria.map((text: string) => ({
        text,
        source: 'ia' as const,
        classification: 'N/A' as CriteriaClassification,
      }));

      setCriteriaList((prev) => [...prev, ...newCriteria]);
      success('Critères extraits', `${result.count} critères trouvés`);
    } catch (err) {
      setError(err as APIError);
      showError('Erreur', 'Échec de l\'extraction');
    } finally {
      setExtractingCriteria(false);
    }
  };

  const handleAddManualCriteria = () => {
    if (!manualCriteriaText.trim()) return;

    const lines = manualCriteriaText.split('\n').filter((line) => line.trim());
    const newCriteria: CriteriaItem[] = lines.map((text) => ({
      text: text.trim(),
      source: 'manual' as const,
      classification: 'Must-have' as CriteriaClassification,
    }));

    setCriteriaList((prev) => [...prev, ...newCriteria]);
    setManualCriteriaText('');
    success('Critères ajoutés', `${lines.length} critères ajoutés`);
  };

  const updateCriteriaClassification = (index: number, classification: CriteriaClassification) => {
    setCriteriaList((prev) => {
      const newList = [...prev];
      newList[index] = { ...newList[index], classification };
      return newList;
    });
  };

  const removeCriteria = (index: number) => {
    setCriteriaList((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSave = async () => {
    if (!projectId || !offreData) return;

    // Intégrer les critères classifiés
    const mustHave = criteriaList
      .filter((c) => c.classification === 'Must-have')
      .map((c) => c.text);
    const niceHave = criteriaList
      .filter((c) => c.classification === 'Nice-to-have')
      .map((c) => c.text);

    const finalOffre: Offre = {
      ...offreData,
      must_have: mustHave,
      nice_have: niceHave,
    };

    setSaving(true);
    try {
      await offresApi.upsert(projectId, finalOffre);
      success('Offre sauvegardée', 'L\'offre complète a été enregistrée');
      return true;
    } catch (err) {
      setError(err as APIError);
      showError('Erreur', 'Impossible de sauvegarder');
      return false;
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAndNext = async () => {
    const saved = await handleSave();
    if (saved) {
      navigate(`/projects/${projectId}/cvs`);
    }
  };

  if (loading) return <LoadingPage text="Chargement..." />;

  const mustHaveCount = criteriaList.filter((c) => c.classification === 'Must-have').length;
  const niceHaveCount = criteriaList.filter((c) => c.classification === 'Nice-to-have').length;

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(`/projects/${projectId}`)}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <div className="text-sm text-muted-foreground mb-1">
            {project?.nom} / Offre d'emploi
          </div>
          <h1 className="text-3xl font-bold tracking-tight">
            {offreData?.sections.titre || 'Nouvelle offre'}
          </h1>
        </div>
        <Button onClick={handleSave} disabled={saving || !offreData}>
          <Save className="mr-2 h-4 w-4" />
          {saving ? 'Enregistrement...' : 'Enregistrer'}
        </Button>
      </div>

      {error && <ErrorBanner error={error} />}

      {/* === SECTION 1: Préparer l'offre === */}
      <Card>
        <CardHeader>
          <CardTitle>1. Préparer l'offre d'emploi</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <Button
              variant={inputMethod === 'text' ? 'default' : 'outline'}
              onClick={() => setInputMethod('text')}
            >
              <FileText className="mr-2 h-4 w-4" />
              Texte
            </Button>
            <Button
              variant={inputMethod === 'file' ? 'default' : 'outline'}
              onClick={() => setInputMethod('file')}
            >
              <Upload className="mr-2 h-4 w-4" />
              Fichier (PDF/DOCX)
            </Button>
          </div>

          {inputMethod === 'text' ? (
            <Textarea
              value={offreText}
              onChange={(e) => setOffreText(e.target.value)}
              placeholder="Collez le texte de l'offre d'emploi ici..."
              rows={12}
            />
          ) : (
            <div className="space-y-2">
              <Input
                type="file"
                accept=".pdf,.docx"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              />
              {selectedFile && (
                <p className="text-sm text-muted-foreground">
                  Fichier sélectionné: {selectedFile.name}
                </p>
              )}
            </div>
          )}

          <Button onClick={handleParseOffre} disabled={parsing} className="w-full">
            {parsing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyse en cours...
              </>
            ) : (
              'Préparer l\'offre'
            )}
          </Button>

          {offreData && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm font-medium text-green-900">
                 Offre parsée avec succès
              </p>
              <details className="mt-2">
                <summary className="text-xs text-green-700 cursor-pointer">
                  Voir le JSON
                </summary>
                <pre className="mt-2 text-xs bg-white p-2 rounded border overflow-auto max-h-60">
                  {JSON.stringify(offreData, null, 2)}
                </pre>
              </details>
            </div>
          )}
        </CardContent>
      </Card>

      {/* === SECTION 2: Enrichissement === */}
      {offreData && (
        <Card>
          <CardHeader>
            <CardTitle>2. Enrichir l'offre (optionnel)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* ROME */}
              <div className="space-y-2">
                <Label>Enrichissement ROME</Label>
                <Button disabled variant="outline" className="w-full">
                  Enrichir avec ROME
                </Button>
                <p className="text-xs text-muted-foreground">
                  (À venir - Référentiel Pôle Emploi)
                </p>
              </div>

              {/* IA */}
              <div className="space-y-2">
                <Label>Enrichissement IA</Label>
                <Button onClick={handleEnrichWithAI} disabled={enriching} className="w-full">
                  {enriching ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Analyse en cours...
                    </>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-4 w-4" />
                      Enrichissement intelligent
                    </>
                  )}
                </Button>
              </div>
            </div>

            {/* Propositions enrichissement */}
            {enrichmentResult && (
              <div className="space-y-4 pt-4 border-t">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">
                    Propositions IA
                    <span className="ml-2 text-sm font-normal text-muted-foreground">
                      (Complétude actuelle : {enrichmentResult.coverage_score}%
                      {enrichmentResult.coverage_score >= 90 && ' - Très complète'}
                      {enrichmentResult.coverage_score >= 70 && enrichmentResult.coverage_score < 90 && ' - Correcte'}
                      {enrichmentResult.coverage_score >= 50 && enrichmentResult.coverage_score < 70 && ' - Incomplète'}
                      {enrichmentResult.coverage_score < 50 && ' - Très lacunaire'})
                    </span>
                  </h3>
                  <Button onClick={handleApplyEnrichment} size="sm">
                    <CheckCircle className="mr-2 h-4 w-4" />
                    Appliquer
                  </Button>
                </div>

                <div className="grid gap-4 max-h-96 overflow-y-auto">
                  {/* Compétences */}
                  {enrichmentResult.propositions.competences.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Compétences</h4>
                      {enrichmentResult.propositions.competences.map((comp, idx) => (
                        <label key={idx} className="flex items-start gap-2 p-2 hover:bg-accent rounded cursor-pointer">
                          <input
                            type="checkbox"
                            checked={selections.competences.includes(idx)}
                            onChange={() => toggleSelection('competences', idx)}
                            className="mt-1"
                          />
                          <div className="flex-1 text-sm">
                            <span className="font-medium">{comp.name}</span>
                            <span className="text-xs text-muted-foreground ml-2">({comp.type})</span>
                            <p className="text-xs text-muted-foreground">{comp.rationale}</p>
                          </div>
                        </label>
                      ))}
                    </div>
                  )}

                  {/* Outils */}
                  {enrichmentResult.propositions.outils.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Outils</h4>
                      {enrichmentResult.propositions.outils.map((outil, idx) => (
                        <label key={idx} className="flex items-start gap-2 p-2 hover:bg-accent rounded cursor-pointer">
                          <input
                            type="checkbox"
                            checked={selections.outils.includes(idx)}
                            onChange={() => toggleSelection('outils', idx)}
                            className="mt-1"
                          />
                          <div className="flex-1 text-sm">
                            <span className="font-medium">{outil.name}</span>
                            <p className="text-xs text-muted-foreground">{outil.rationale}</p>
                          </div>
                        </label>
                      ))}
                    </div>
                  )}

                  {/* Langages */}
                  {enrichmentResult.propositions.langages.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Langages</h4>
                      {enrichmentResult.propositions.langages.map((lang, idx) => (
                        <label key={idx} className="flex items-start gap-2 p-2 hover:bg-accent rounded cursor-pointer">
                          <input
                            type="checkbox"
                            checked={selections.langages.includes(idx)}
                            onChange={() => toggleSelection('langages', idx)}
                            className="mt-1"
                          />
                          <div className="flex-1 text-sm">
                            <span className="font-medium">{lang.name}</span>
                            <p className="text-xs text-muted-foreground">{lang.rationale}</p>
                          </div>
                        </label>
                      ))}
                    </div>
                  )}

                  {/* Certifications */}
                  {enrichmentResult.propositions.certifications.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Certifications</h4>
                      {enrichmentResult.propositions.certifications.map((cert, idx) => (
                        <label key={idx} className="flex items-start gap-2 p-2 hover:bg-accent rounded cursor-pointer">
                          <input
                            type="checkbox"
                            checked={selections.certifications.includes(idx)}
                            onChange={() => toggleSelection('certifications', idx)}
                            className="mt-1"
                          />
                          <div className="flex-1 text-sm">
                            <span className="font-medium">{cert.name}</span>
                            <p className="text-xs text-muted-foreground">{cert.rationale}</p>
                          </div>
                        </label>
                      ))}
                    </div>
                  )}

                  {/* Missions */}
                  {enrichmentResult.propositions.missions.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Missions complémentaires</h4>
                      {enrichmentResult.propositions.missions.map((mission, idx) => (
                        <label key={idx} className="flex items-start gap-2 p-2 hover:bg-accent rounded cursor-pointer">
                          <input
                            type="checkbox"
                            checked={selections.missions.includes(idx)}
                            onChange={() => toggleSelection('missions', idx)}
                            className="mt-1"
                          />
                          <div className="flex-1 text-sm">
                            <span className="font-medium">{mission.text}</span>
                            <p className="text-xs text-muted-foreground">{mission.rationale}</p>
                          </div>
                        </label>
                      ))}
                    </div>
                  )}

                  {/* Questions */}
                  {enrichmentResult.propositions.questions_clarification.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Questions de clarification</h4>
                      {enrichmentResult.propositions.questions_clarification.map((q, idx) => (
                        <div key={idx} className="space-y-1 mb-3">
                          <Label className="text-xs">{q}</Label>
                          <Input
                            value={questionResponses[q] || ''}
                            onChange={(e) =>
                              setQuestionResponses({ ...questionResponses, [q]: e.target.value })
                            }
                            placeholder="Votre réponse..."
                            className="text-sm"
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* === SECTION 3: Must-have / Nice-have === */}
      {offreData && (
        <Card>
          <CardHeader>
            <CardTitle>3. Définir les critères de sélection</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Extraction IA */}
              <div className="space-y-2">
                <Label>Extraction automatique par IA</Label>
                <Button
                  onClick={handleExtractCriteria}
                  disabled={extractingCriteria}
                  variant="outline"
                  className="w-full"
                >
                  {extractingCriteria ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Extraction...
                    </>
                  ) : (
                    'Extraire les critères avec IA'
                  )}
                </Button>
              </div>

              {/* Saisie manuelle */}
              <div className="space-y-2">
                <Label>Saisie manuelle</Label>
                <Textarea
                  value={manualCriteriaText}
                  onChange={(e) => setManualCriteriaText(e.target.value)}
                  placeholder="Un critère par ligne&#10;Ex: Python&#10;5 ans d'expérience&#10;Bac+5"
                  rows={3}
                />
                <Button onClick={handleAddManualCriteria} variant="outline" className="w-full" size="sm">
                  <Plus className="mr-2 h-3 w-3" />
                  Ajouter
                </Button>
              </div>
            </div>

            {/* Liste des critères */}
            {criteriaList.length > 0 && (
              <div className="space-y-3 pt-4 border-t">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium">
                    Classifier les critères ({criteriaList.length})
                  </h4>
                  <div className="text-xs text-muted-foreground space-x-4">
                    <span className="text-red-600 font-medium">
                      Must-have: {mustHaveCount}
                    </span>
                    <span className="text-orange-600 font-medium">
                      Nice-to-have: {niceHaveCount}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-muted-foreground">
                  Must-have = éliminatoire | Nice-to-have = malus | N/A = ignoré
                </p>

                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {criteriaList.map((criteria, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 p-2 border rounded hover:bg-accent"
                    >
                      <span className="flex-1 text-sm">
                        {criteria.text}
                        <span className="ml-2 text-xs text-muted-foreground">
                          ({criteria.source === 'ia' ? 'IA' : 'Manuel'})
                        </span>
                      </span>
                      <Select
                        value={criteria.classification}
                        onChange={(e) =>
                          updateCriteriaClassification(
                            idx,
                            e.target.value as CriteriaClassification
                          )
                        }
                        className="w-40"
                      >
                        <option value="N/A">N/A</option>
                        <option value="Must-have">Must-have</option>
                        <option value="Nice-to-have">Nice-to-have</option>
                      </Select>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => removeCriteria(idx)}
                        className="h-8 w-8"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Bouton Étape suivante en bas */}
      {offreData && (
        <div className="flex justify-end pt-6">
          <Button onClick={handleSaveAndNext} size="lg" disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Sauvegarde en cours...
              </>
            ) : (
              <>
                Étape suivante : Base de CVs
                <ArrowRight className="ml-2 h-5 w-5" />
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
};
