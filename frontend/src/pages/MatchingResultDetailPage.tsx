import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, FileJson, FileSpreadsheet, ChevronDown, ChevronRight, FileText } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from '../components/ui/card';
import { LoadingPage } from '../components/shared/Loading';
import { ErrorBanner } from '../components/shared/ErrorBanner';
import { EvidencePanel } from '../components/matching/EvidencePanel';
import { renderTextWithEvidences } from '../components/matching/renderTextWithEvidences';
import { InterviewSheetButton } from '../components/interview/InterviewSheetButton';
import { matchingApi } from '../api/matching';
import { API_BASE_URL } from '../api/client';
import type { ResultatMatching, APIError } from '../api/types';

export const MatchingResultDetailPage: React.FC = () => {
  const { projectId, timestamp } = useParams<{ projectId: string; timestamp: string }>();
  const navigate = useNavigate();

  const [results, setResults] = useState<ResultatMatching[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<APIError | null>(null);
  const [exporting, setExporting] = useState(false);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  useEffect(() => {
    const fetchResults = async () => {
      if (!projectId || !timestamp) return;

      try {
        setLoading(true);
        setError(null);
        const data = await matchingApi.getResults(projectId, timestamp);
        setResults(data);
      } catch (err) {
        setError(err as APIError);
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [projectId, timestamp]);

  const toggleRowExpansion = (cv: string) => {
    setExpandedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(cv)) {
        newSet.delete(cv);
      } else {
        newSet.add(cv);
      }
      return newSet;
    });
  };

  const handleExportExcel = async () => {
    if (!projectId || !timestamp) return;
    setExporting(true);
    try {
      const blob = await matchingApi.exportExcel(projectId, timestamp);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `matching_${projectId}_${timestamp}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err as APIError);
    } finally {
      setExporting(false);
    }
  };

  const handleExportJSON = async () => {
    if (!projectId || !timestamp) return;
    setExporting(true);
    try {
      const data = await matchingApi.exportJSON(projectId, timestamp);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `matching_${projectId}_${timestamp}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err as APIError);
    } finally {
      setExporting(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 font-bold';
    if (score >= 60) return 'text-blue-600 font-semibold';
    if (score >= 40) return 'text-yellow-600';
    return 'text-gray-600';
  };

  if (loading) return <LoadingPage text="Loading results..." />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(-1)}
          aria-label="Go back"
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight">Matching results</h1>
          <p className="text-muted-foreground">
            {timestamp?.replace('_', ' at ').replace(/-/g, ':')}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportExcel}
            disabled={exporting}
          >
            <FileSpreadsheet className="mr-2 h-4 w-4" />
            Export Excel
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportJSON}
            disabled={exporting}
          >
            <FileJson className="mr-2 h-4 w-4" />
            Export JSON
          </Button>
        </div>
      </div>

      {error && <ErrorBanner error={error} />}

      {/* Results */}
      <Card>
        <CardHeader>
          <CardTitle>{results.length} candidate(s) found</CardTitle>
          <CardDescription>Click a row to view the full details</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[40px]"></TableHead>
                  <TableHead>Rank</TableHead>
                  <TableHead>Resume</TableHead>
                  <TableHead className="w-[60px]">Original</TableHead>
                  <TableHead>Final score</TableHead>
                  <TableHead>Base score</TableHead>
                  <TableHead>Nice-to-have bonus</TableHead>
                  <TableHead>Quality coefficient</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {results.map((result, index) => {
                  // Detect if reranking failed (fallback)
                  const isRerankFallback = result.commentaire_scoring?.includes('⚠️ Re-ranking LLM indisponible');
                  const displayName = result.candidate_name || result.cv;

                  return (
                  <>
                    <TableRow
                      key={result.cv}
                      className="cursor-pointer hover:bg-accent"
                      onClick={() => toggleRowExpansion(result.cv)}
                    >
                      <TableCell>
                        {expandedRows.has(result.cv) ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </TableCell>
                      <TableCell className="font-medium">{index + 1}</TableCell>
                      <TableCell className="font-mono text-xs">
                        <div className="flex items-center gap-2">
                          {displayName}
                          {isRerankFallback && (
                            <Badge variant="outline" className="text-orange-600 border-orange-400 text-xs">
                              ⚠️ Fallback
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell onClick={(e) => e.stopPropagation()}>
                        {result.original_cv_url ? (
                          <a
                            href={`${API_BASE_URL}${result.original_cv_url}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-block"
                          >
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <FileText className="h-4 w-4" />
                            </Button>
                          </a>
                        ) : (
                          <span className="text-muted-foreground text-xs">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className={getScoreColor(result.score_final * 100)}>
                          {(result.score_final * 100).toFixed(1)}
                        </span>
                      </TableCell>
                      <TableCell>{(result.score_base * 100).toFixed(1)}</TableCell>
                      <TableCell>
                        {result.bonus_nice_have_multiplicateur.toFixed(2)}x
                      </TableCell>
                      <TableCell>
                        {result.coefficient_qualite_experience.toFixed(2)}x
                      </TableCell>
                    </TableRow>
                    {expandedRows.has(result.cv) && (
                      <TableRow>
                        <TableCell colSpan={8} className="bg-muted/50">
                          <div className="p-4 space-y-4">
                            {/* Formula */}
                            <div className="bg-background p-3 rounded border">
                              <p className="text-sm font-semibold mb-2">Calculation formula</p>
                              <p className="text-sm font-mono">
                                Final score = {result.score_base.toFixed(3)} × {result.bonus_nice_have_multiplicateur.toFixed(2)} × {result.coefficient_qualite_experience.toFixed(2)} = {result.score_final.toFixed(3)}
                              </p>
                            </div>

                            {/* Missing nice-to-haves */}
                            {result.nice_have_manquants && result.nice_have_manquants.length > 0 && (
                              <div>
                                <p className="text-sm font-semibold mb-2">Missing nice-to-haves</p>
                                <div className="flex flex-wrap gap-2">
                                  {result.nice_have_manquants.map((nh) => (
                                    <Badge key={nh} variant="outline">{nh}</Badge>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Scoring commentary */}
                            {result.commentaire_scoring && (
                              <div>
                                <p className="text-sm font-semibold mb-2">Scoring commentary</p>
                                <div className="text-sm text-muted-foreground whitespace-pre-wrap">
                                  {renderTextWithEvidences(result.commentaire_scoring, result.evidences)}
                                </div>
                              </div>
                            )}

                            {/* HR appreciation */}
                            {result.appreciation_globale && (
                              <div>
                                <p className="text-sm font-semibold mb-2">HR appreciation</p>
                                <div className="text-sm text-muted-foreground whitespace-pre-wrap">
                                  {renderTextWithEvidences(
                                    result.appreciation_globale.startsWith(displayName)
                                      ? result.appreciation_globale
                                      : `${displayName} — ${result.appreciation_globale}`,
                                    result.evidences
                                  )}
                                </div>
                              </div>
                            )}

                            {/* Evidences and flags */}
                            <EvidencePanel
                              evidences={result.evidences}
                              flags={result.flags}
                              className="mt-2"
                            />

                            {/* Prepare interview button */}
                            {projectId && timestamp && (
                              <div className="mt-4">
                                <InterviewSheetButton
                                  candidateId={result.cv}
                                  jobId={projectId}
                                  matchingId={timestamp}
                                  variant="default"
                                  size="sm"
                                />
                              </div>
                            )}

                            {/* Warning if reranking fallback */}
                            {isRerankFallback && (
                              <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-3 mt-4">
                                <p className="text-sm text-orange-800 dark:text-orange-200">
                                  <strong>ℹ️ Note:</strong> The qualitative HR analysis could not be generated because the reranking service failed.
                                  Quantitative scores (embeddings + nice-to-haves) remain valid and reliable.
                                  The quality coefficient is fixed at 1.0 (neutral). Alert flags (gaps/overlaps) are detected automatically when available.
                                </p>
                              </div>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
