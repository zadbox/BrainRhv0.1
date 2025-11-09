import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useSearchParams, useParams } from 'react-router-dom';
import { Upload, FileText, Trash2, ArrowRight, ArrowLeft, Search, ChevronDown, ChevronUp, Filter } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Select } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '../components/ui/card';
import { LoadingPage } from '../components/shared/Loading';
import { ErrorBanner } from '../components/shared/ErrorBanner';
import { EmptyState } from '../components/shared/EmptyState';
import { cvsApi } from '../api/cvs';
import type { CV, APIError } from '../api/types';
import { cn } from '../lib/utils';

export const CVBasePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { projectId: urlProjectId } = useParams<{ projectId: string }>();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // If we arrive from a project (URL), preload that project. Otherwise default to "all"
  const [selectedProjectId, setSelectedProjectId] = useState<string>(urlProjectId || searchParams.get('project') || 'tous');
  const [cvs, setCvs] = useState<CV[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<APIError | null>(null);
  const [dragging, setDragging] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedCVs, setExpandedCVs] = useState<Set<string>>(new Set());
  const [filterCompetence, setFilterCompetence] = useState('');
  // Company filter: "all" by default
  const [filterEntreprise, setFilterEntreprise] = useState<string>('tout');
  // Parsing progress state
  const [parsing, setParsing] = useState(false);
  const [parsingProgress, setParsingProgress] = useState({ current: 0, total: 0 });


  const fetchCVs = useCallback(async (projectId: string) => {
    try {
      setLoading(true);
      setError(null);

      // If projectId is "all", fetch every resume
      if (projectId === 'tous') {
        const data = await cvsApi.getAll();
        setCvs(data);
      } else {
        const data = await cvsApi.getByProject(projectId);
        setCvs(data);
      }
    } catch (err) {
      console.error('Failed to fetch CVs:', err);
      setError({
        code: 'CV_FETCH_ERROR',
        message: err instanceof Error ? err.message : 'Unable to fetch resumes',
        details: err,
      });
      setCvs([]);
    } finally {
      setLoading(false);
    }
  }, []);


  // Update selectedProjectId whenever urlProjectId changes
  useEffect(() => {
    if (urlProjectId && urlProjectId !== selectedProjectId) {
      setSelectedProjectId(urlProjectId);
    }
  }, [urlProjectId, selectedProjectId]);

  useEffect(() => {
    if (selectedProjectId) {
      fetchCVs(selectedProjectId);
    } else {
      setCvs([]);
      setLoading(false);
    }
  }, [selectedProjectId, fetchCVs]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files) {
      setSelectedFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => {
    setDragging(false);
  };

  const handleUploadAndParse = async () => {
    console.log('🔵 handleUploadAndParse called');
    console.log('📁 selectedFiles:', selectedFiles);
    console.log('📂 selectedProjectId:', selectedProjectId);

    // Prevent double-clicks
    if (parsing) {
      console.log('⚠️ Parsing already in progress, ignoring click');
      return;
    }

    if (selectedFiles.length === 0) {
      console.log('❌ No files selected');
      setError({
        message: 'Please select at least one resume file before continuing.',
        code: 'NO_FILES_SELECTED'
      });
      return;
    }

    if (!selectedProjectId || selectedProjectId === 'tous') {
      console.log('❌ No project selected');
      setError({
        message: 'Please select a specific project to upload resumes.',
        code: 'NO_PROJECT_SELECTED'
      });
      return;
    }

    console.log('✅ Validation passed, starting upload...');

    setParsing(true);
    setParsingProgress({ current: 0, total: selectedFiles.length });
    setError(null);

    try {
      // Upload files via FormData + SSE parsing
      const formData = new FormData();
      selectedFiles.forEach((file) => {
        formData.append('files', file);
      });
      console.log('📦 FormData created with', selectedFiles.length, 'files');

      const urlParams = new URLSearchParams({ model: 'gpt-4o-mini' });
      urlParams.append('project_id', selectedProjectId);
      const url = `${cvsApi.getParseStreamUrl()}?${urlParams.toString()}`;
      console.log('🌐 Fetch URL:', url);

      console.log('⏳ Starting fetch...');
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });
      console.log('📨 Response received:', response.status, response.statusText);

      if (!response.ok) {
        const errorText = await response.text();
        console.log('❌ Response not OK:', errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      console.log('✅ Response OK, starting to read stream...');

      // Read SSE stream and update progress
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        console.log('❌ No response body/reader');
        throw new Error('No response body');
      }

      console.log('📖 Reader created, starting to read chunks...');
      let buffer = '';
      let chunkCount = 0;
      while (true) {
        const { done, value } = await reader.read();
        chunkCount++;
        console.log(`📦 Chunk ${chunkCount} received:`, { done, valueLength: value?.length });

        if (done) {
          console.log('✅ Stream reading done');
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        console.log(`📝 Processing ${lines.length} SSE lines`);
        for (const line of lines) {
          if (!line.trim()) continue;

          const eventMatch = line.match(/^event: (.+)$/m);
          const dataMatch = line.match(/^data: (.+)$/m);

          if (eventMatch && dataMatch) {
            const eventType = eventMatch[1];
            const data = JSON.parse(dataMatch[1]);
            console.log(`🎯 SSE Event: ${eventType}`, data);

            if (eventType === 'progress') {
              setParsingProgress({ current: data.current, total: data.total });
            } else if (eventType === 'done') {
              console.log('✅ Received "done" event, breaking loop');
              break;
            }
          }
        }
      }

      console.log('✅ Parsing complete, refreshing resumes...');
      
      // Refresh CV list with a short delay to ensure the API has finished
      setTimeout(async () => {
        try {
          await fetchCVs(selectedProjectId);
          console.log('✅ Resumes reloaded successfully');
        } catch (refreshErr) {
          console.error('❌ Erreur lors du rechargement:', refreshErr);
        }
      }, 500);

      // Clear selected files
      setSelectedFiles([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

    } catch (err) {
      console.error('❌ Parsing error:', err);
      setError({ code: 'PARSE_ERROR', message: String(err) });
    } finally {
      setParsing(false);
      setParsingProgress({ current: 0, total: 0 });
    }
  };

  const handleDeleteCV = async (cvId: string) => {
    try {
      await cvsApi.delete(cvId);
      if (selectedProjectId) {
        await fetchCVs(selectedProjectId);
      }
    } catch (err) {
      setError(err as APIError);
    }
  };

  const toggleCVExpand = (cvId: string) => {
    setExpandedCVs(prev => {
      const next = new Set(prev);
      if (next.has(cvId)) {
        next.delete(cvId);
      } else {
        next.add(cvId);
      }
      return next;
    });
  };

  // Extraire la liste unique des entreprises depuis les projets des CVs
  const uniqueEntreprises = Array.from(
    new Set(
      cvs
        .filter(cv => cv.enterprise_nom)
        .map(cv => cv.enterprise_nom!)
    )
  ).sort();

  // Filter CVs based on search and filters
  // Si on arrive depuis un projet (urlProjectId), pas de filtre entreprise
  const filteredCVs = cvs.filter(cv => {
    const matchesSearch =
      !searchQuery ||
      cv.identite?.nom?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      cv.identite?.prenom?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      cv.identite?.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      cv.titre?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      cv.cv.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCompetence =
      !filterCompetence ||
      cv.competences_techniques.some(c => c.toLowerCase().includes(filterCompetence.toLowerCase())) ||
      cv.competences_transversales.some(c => c.toLowerCase().includes(filterCompetence.toLowerCase()));

    // Apply company filter only when coming from the sidebar (no urlProjectId)
    const matchesEntreprise = urlProjectId
      ? true  // Pas de filtre entreprise si on vient d'un projet
      : (!filterEntreprise || filterEntreprise === 'tout' || cv.enterprise_nom === filterEntreprise);

    return matchesSearch && matchesCompetence && matchesEntreprise;
  });

  if (loading && selectedProjectId) return <LoadingPage text="Loading resumes..." />;

  return (
    <div className="space-y-6">
      {/* Header with back button if navigating from a specific project */}
      {urlProjectId ? (
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(`/projects/${urlProjectId}`)}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Project CV library</h1>
              <p className="text-muted-foreground">Manage and upload resumes</p>
            </div>
            {cvs.length > 0 && (
              <Button
                onClick={() => navigate(`/projects/${urlProjectId}/matching`)}
                size="lg"
              >
                Next step: Matching
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            )}
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">CV library</h1>
            <p className="text-muted-foreground">Manage and upload resumes</p>
          </div>
        </div>
      )}

      {error && <ErrorBanner error={error} />}

      {/* File Upload Area */}
      <Card>
        <CardHeader>
          <CardTitle>Resume upload</CardTitle>
          <CardDescription>
            Drag and drop your PDF or DOCX files, or click to browse
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className={cn(
              'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
              dragging ? 'border-primary bg-primary/5' : 'border-border',
              'hover:border-primary hover:bg-accent/50'
            )}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-sm font-medium mb-2">
              Drag and drop your files here, or click to browse
            </p>
            <p className="text-xs text-muted-foreground">
              Supported formats: PDF, DOCX (max 10MB per file)
            </p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>

          {selectedFiles.length > 0 && (
            <div className="mt-4 space-y-2">
              <p className="text-sm font-medium">{selectedFiles.length} file(s) selected:</p>
              <div className="space-y-1">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="flex items-center gap-2 text-sm">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="flex-1 truncate">{file.name}</span>
                    <Badge variant="secondary">{(file.size / 1024).toFixed(1)} KB</Badge>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex-col gap-3">
          <Button
            onClick={handleUploadAndParse}
            className="w-full"
            size="lg"
            disabled={parsing || selectedFiles.length === 0}
          >
            <Upload className="mr-2 h-5 w-5" />
            {parsing ? 'Parsing in progress...' : 'Upload resumes'}
          </Button>

          {/* Progress bar */}
          {parsing && (
            <div className="w-full space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  Parsing resumes: {parsingProgress.current} / {parsingProgress.total}
                </span>
                <span className="font-medium">
                  {Math.round((parsingProgress.current / parsingProgress.total) * 100)}%
                </span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2.5 overflow-hidden">
                <div
                  className="bg-primary h-2.5 rounded-full transition-all duration-300"
                  style={{ width: `${(parsingProgress.current / parsingProgress.total) * 100}%` }}
                />
              </div>
            </div>
          )}
        </CardFooter>
      </Card>

      {/* CVs List */}
      {selectedProjectId && selectedProjectId !== '' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              Parsed resumes ({filteredCVs.length}/{cvs.length})
            </h2>
          </div>

          {/* Search and Filters */}
          {cvs.length > 0 && (
            <Card>
              <CardContent className="pt-6">
                <div className={`grid grid-cols-1 gap-4 ${urlProjectId ? 'md:grid-cols-2' : 'md:grid-cols-3'}`}>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search by name, email, title..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                  <div className="relative">
                    <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Filter by skill..."
                      value={filterCompetence}
                      onChange={(e) => setFilterCompetence(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                  {/* Company filter only when coming from the sidebar */}
                  {!urlProjectId && (
                    <Select
                      value={filterEntreprise}
                      onChange={(e) => setFilterEntreprise(e.target.value)}
                    >
                      <option value="tout">All companies</option>
                      {uniqueEntreprises.map((entreprise) => (
                        <option key={entreprise} value={entreprise}>
                          {entreprise}
                        </option>
                      ))}
                    </Select>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {cvs.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="No resumes yet"
              description="Parse resumes for this project to get started"
            />
          ) : filteredCVs.length === 0 ? (
            <EmptyState
              icon={Search}
              title="No results"
              description="No resume matches your filters"
            />
          ) : (
            <div className="space-y-3">
              {filteredCVs.map((cv) => {
                const isExpanded = expandedCVs.has(cv.cv);
                return (
                  <Card key={cv.cv}>
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-base">
                            {cv.identite?.prenom} {cv.identite?.nom || cv.cv}
                          </CardTitle>
                          <CardDescription>
                            {cv.titre || 'No title'}
                          </CardDescription>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleCVExpand(cv.cv)}
                        >
                          {isExpanded ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3 text-sm">
                        {cv.identite?.email && (
                          <p className="text-muted-foreground">{cv.identite.email}</p>
                        )}
                        {cv.identite?.telephone && (
                          <p className="text-muted-foreground">{cv.identite.telephone}</p>
                        )}

                        {/* Technical skills */}
                        {cv.competences_techniques.length > 0 && (
                          <div>
                            <p className="font-medium mb-1">Technical skills</p>
                            <div className="flex flex-wrap gap-1">
                              {(isExpanded ? cv.competences_techniques : cv.competences_techniques.slice(0, 5)).map((comp, idx) => (
                                <Badge key={idx} variant="secondary" className="text-xs">
                                  {comp}
                                </Badge>
                              ))}
                              {!isExpanded && cv.competences_techniques.length > 5 && (
                                <Badge variant="outline" className="text-xs">
                                  +{cv.competences_techniques.length - 5}
                                </Badge>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Expanded details - full JSON */}
                        {isExpanded && (
                          <div className="pt-3 border-t">
                            <p className="text-xs font-medium mb-2">Full JSON structure:</p>
                            <pre className="text-xs bg-muted p-3 rounded overflow-x-auto max-h-96 overflow-y-auto">
                              {JSON.stringify(cv, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    </CardContent>
                    <CardFooter className="pt-3">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteCV(cv.cv)}
                        className="w-full text-destructive hover:text-destructive"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                      </Button>
                    </CardFooter>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
