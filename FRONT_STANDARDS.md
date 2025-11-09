# 🎨 STANDARDS FRONTEND — Brain RH Migration

**Stack:** React 18 + TypeScript + Vite + Radix UI / shadcn/ui
**Objectif:** Application pro niveau assistant RH, accessible, performante, maintenable

---

## 📐 ARCHITECTURE & CODE (React + TypeScript)

### Principes fondamentaux

#### 1. TypeScript obligatoire
```typescript
// ✅ BON - Types stricts, pas de 'any'
interface CVUploadProps {
  files: File[];
  onFilesSelected: (files: File[]) => void;
  maxSize?: number;
  disabled?: boolean;
}

export const CVUpload: React.FC<CVUploadProps> = ({ files, onFilesSelected, maxSize = 5000000, disabled = false }) => {
  // ...
}

// ❌ MAUVAIS - Pas de types
export const CVUpload = ({ files, onFilesSelected, maxSize, disabled }) => {
  // ...
}
```

**Référence:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

#### 2. Composants purs UI + logique dans hooks
```typescript
// ✅ BON - Séparation claire UI / logique
// hooks/useCVParsing.ts
export const useCVParsing = () => {
  const [parsing, setParsing] = useState(false);
  const [results, setResults] = useState<CV[]>([]);
  const [error, setError] = useState<string | null>(null);

  const parseFiles = async (files: File[]) => {
    setParsing(true);
    setError(null);
    try {
      const response = await parseCVs(files);
      setResults(response.results);
    } catch (err) {
      setError(err.message);
    } finally {
      setParsing(false);
    }
  };

  return { parsing, results, error, parseFiles };
};

// components/CVParsingPage.tsx
export const CVParsingPage: React.FC = () => {
  const { parsing, results, error, parseFiles } = useCVParsing();

  return (
    <div>
      <CVUploader onFilesSelected={parseFiles} disabled={parsing} />
      {error && <ErrorBanner message={error} />}
      {results.length > 0 && <CVList cvs={results} />}
    </div>
  );
};

// ❌ MAUVAIS - Tout mélangé dans le composant
export const CVParsingPage = () => {
  const [parsing, setParsing] = useState(false);
  const [results, setResults] = useState([]);
  // 200 lignes de logique mélangée avec JSX...
};
```

**Référence:** [React Patterns](https://reactpatterns.com/)

#### 3. Éviter useEffect inutiles
```typescript
// ✅ BON - Calcul dérivé direct (pas d'effet)
const CVList: React.FC<{ cvs: CV[] }> = ({ cvs }) => {
  const sortedCVs = useMemo(
    () => [...cvs].sort((a, b) => b.score_final - a.score_final),
    [cvs]
  );

  return (
    <ul>
      {sortedCVs.map(cv => <CVCard key={cv.cv} cv={cv} />)}
    </ul>
  );
};

// ❌ MAUVAIS - useEffect inutile pour calculer un dérivé
const CVList = ({ cvs }) => {
  const [sortedCVs, setSortedCVs] = useState([]);

  useEffect(() => {
    setSortedCVs([...cvs].sort((a, b) => b.score_final - a.score_final));
  }, [cvs]); // Crée un état superflu + effet non nécessaire

  return <ul>{sortedCVs.map(...)}</ul>;
};
```

**RÈGLE:** useEffect uniquement pour synchroniser avec un système externe (fetch, SSE, WebSocket, DOM, timers).

**Référence:** [You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect)

#### 4. État minimal
```typescript
// ✅ BON - Un seul état source, le reste dérivé
interface MatchingState {
  cvs: CV[];
  offre: Offre;
  topRerank: number;
  results: ResultatMatching[] | null;
  loading: boolean;
  error: string | null;
}

const useMatching = () => {
  const [state, setState] = useState<MatchingState>({
    cvs: [],
    offre: null,
    topRerank: 10,
    results: null,
    loading: false,
    error: null
  });

  // Dérivés calculés à la volée
  const topResults = state.results?.slice(0, state.topRerank) ?? [];
  const hasResults = (state.results?.length ?? 0) > 0;

  return { ...state, topResults, hasResults, setState };
};

// ❌ MAUVAIS - États dupliqués et désynchronisés
const [results, setResults] = useState([]);
const [topResults, setTopResults] = useState([]); // Doublon!
const [hasResults, setHasResults] = useState(false); // Doublon!

useEffect(() => {
  setTopResults(results.slice(0, 10));
  setHasResults(results.length > 0);
}, [results]); // Synchronisation manuelle = source de bugs
```

**Référence:** [Choosing the State Structure](https://react.dev/learn/choosing-the-state-structure)

---

## 🎨 UX/UI PROFESSIONNELLE

### 1. Design System (tokens + composants Radix/shadcn)

#### Tokens de design
```css
/* styles/tokens.css */
:root {
  /* Couleurs (échelle Material Design) */
  --color-primary-50: #E3F2FD;
  --color-primary-100: #BBDEFB;
  --color-primary-500: #2196F3;
  --color-primary-700: #1976D2;
  --color-primary-900: #0D47A1;

  --color-gray-50: #FAFAFA;
  --color-gray-100: #F5F5F5;
  --color-gray-500: #9E9E9E;
  --color-gray-700: #616161;
  --color-gray-900: #212121;

  --color-success-500: #4CAF50;
  --color-error-500: #F44336;
  --color-warning-500: #FF9800;

  /* Espacements (grille 8px) */
  --spacing-1: 0.25rem; /* 4px */
  --spacing-2: 0.5rem;  /* 8px */
  --spacing-3: 0.75rem; /* 12px */
  --spacing-4: 1rem;    /* 16px */
  --spacing-6: 1.5rem;  /* 24px */
  --spacing-8: 2rem;    /* 32px */
  --spacing-12: 3rem;   /* 48px */

  /* Typographie */
  --font-family-base: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  --font-family-mono: 'Fira Code', 'Consolas', monospace;

  --font-size-xs: 0.75rem;   /* 12px */
  --font-size-sm: 0.875rem;  /* 14px */
  --font-size-base: 1rem;    /* 16px */
  --font-size-lg: 1.125rem;  /* 18px */
  --font-size-xl: 1.25rem;   /* 20px */
  --font-size-2xl: 1.5rem;   /* 24px */
  --font-size-3xl: 1.875rem; /* 30px */
  --font-size-4xl: 2.25rem;  /* 36px */

  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;

  /* Ombres */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);

  /* Bordures */
  --radius-sm: 0.25rem;  /* 4px */
  --radius-md: 0.5rem;   /* 8px */
  --radius-lg: 0.75rem;  /* 12px */
  --radius-full: 9999px;

  /* Transitions */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);
}
```

**Référence:** [Material Design Tokens](https://m3.material.io/foundations/design-tokens/overview), [Carbon Design System](https://carbondesignsystem.com/guidelines/spacing/overview/)

#### Composants shadcn/ui (accessibles par défaut)
```bash
# Installation shadcn/ui
npx shadcn-ui@latest init

# Ajouter composants nécessaires
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add form
npx shadcn-ui@latest add table
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add progress
npx shadcn-ui@latest add select
npx shadcn-ui@latest add dropdown-menu
```

**Avantages:**
- Accessibilité intégrée (Radix Primitives + WAI-ARIA)
- Navigation clavier complète
- Focus management automatique
- Composants copiables et customisables

**Référence:** [shadcn/ui](https://ui.shadcn.com/), [Radix UI](https://www.radix-ui.com/)

### 2. Typographie & hiérarchie

```typescript
// components/Typography.tsx
export const Typography = {
  H1: ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <h1 className={`text-4xl font-bold leading-tight text-gray-900 ${className}`}>
      {children}
    </h1>
  ),

  H2: ({ children, className = "" }) => (
    <h2 className={`text-3xl font-semibold leading-tight text-gray-900 ${className}`}>
      {children}
    </h2>
  ),

  H3: ({ children, className = "" }) => (
    <h3 className={`text-2xl font-semibold leading-normal text-gray-900 ${className}`}>
      {children}
    </h3>
  ),

  Body: ({ children, className = "" }) => (
    <p className={`text-base leading-relaxed text-gray-700 ${className}`}>
      {children}
    </p>
  ),

  Small: ({ children, className = "" }) => (
    <span className={`text-sm leading-normal text-gray-600 ${className}`}>
      {children}
    </span>
  ),

  Caption: ({ children, className = "" }) => (
    <span className={`text-xs leading-normal text-gray-500 ${className}`}>
      {children}
    </span>
  ),
};

// Usage
<Typography.H1>Parser des CVs</Typography.H1>
<Typography.Body>
  Glissez-déposez vos fichiers PDF ou DOCX pour les analyser automatiquement.
</Typography.Body>
```

**Référence:** [Material Design Typography](https://m3.material.io/styles/typography/overview), [Carbon Typography](https://carbondesignsystem.com/guidelines/typography/overview)

### 3. Formulaires accessibles

```typescript
// components/CVClassificationForm.tsx
import { Label } from "@/components/ui/label";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";

interface Critere {
  id: string;
  text: string;
  source: "manuel" | "ia";
}

export const CVClassificationForm: React.FC<{ criteres: Critere[] }> = ({ criteres }) => {
  const [classifications, setClassifications] = useState<Record<string, string>>({});

  return (
    <form className="space-y-4">
      {criteres.map(critere => (
        <div key={critere.id} className="flex items-center gap-4">
          {/* Label associé au contrôle (accessibilité) */}
          <Label htmlFor={`classification-${critere.id}`} className="flex-1">
            <span className="text-xs text-gray-500 font-mono">
              [{critere.source === "manuel" ? "Manuel" : "IA"}]
            </span>
            {" "}
            {critere.text}
          </Label>

          {/* Select accessible (Radix) */}
          <Select
            value={classifications[critere.id] || "N/A"}
            onValueChange={(value) => {
              setClassifications(prev => ({ ...prev, [critere.id]: value }));
            }}
          >
            <SelectTrigger id={`classification-${critere.id}`} className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="N/A">N/A</SelectItem>
              <SelectItem value="Must-have">Must-have</SelectItem>
              <SelectItem value="Nice-to-have">Nice-to-have</SelectItem>
            </SelectContent>
          </Select>
        </div>
      ))}
    </form>
  );
};
```

**Bonnes pratiques:**
- Labels explicites (pas de placeholder seul)
- Erreurs inline associées au champ (aria-describedby)
- Focus automatique sur premier champ invalide
- Microcopy courte et utile

**Référence:** [Radix Form](https://www.radix-ui.com/primitives/docs/components/form), [Nielsen Norman Group - Form Design](https://www.nngroup.com/articles/web-form-design/)

### 4. Microcopy (textes courts et utiles)

```typescript
// ✅ BON - Clair, actionnable, sans jargon
<Button onClick={handleParse}>
  Analyser les CVs
</Button>

<ErrorMessage>
  Impossible de parser ce fichier. Vérifiez qu'il s'agit d'un PDF ou DOCX valide.
</ErrorMessage>

<ProgressIndicator>
  Analyse en cours... 3 sur 10 CVs traités
</ProgressIndicator>

// ❌ MAUVAIS - Technique, vague, jargon
<Button onClick={handleParse}>
  Exécuter pipeline LLM
</Button>

<ErrorMessage>
  Exception lors de l'extraction (ERR_PARSE_001)
</ErrorMessage>

<ProgressIndicator>
  Processing...
</ProgressIndicator>
```

**Référence:** [Microcopy Best Practices (NN/g)](https://www.nngroup.com/articles/microcopy/)

---

## ⚡ PERFORMANCE (Core Web Vitals)

### Objectifs chiffrés (mesurables)

| Métrique | Cible | Mesure |
|----------|-------|--------|
| **LCP** (Largest Contentful Paint) | < 2.5s | Lighthouse / WebPageTest |
| **CLS** (Cumulative Layout Shift) | < 0.1 | Lighthouse |
| **INP** (Interaction to Next Paint) | < 200ms | Chrome DevTools |
| **FCP** (First Contentful Paint) | < 1.8s | Lighthouse |

**Référence:** [Web.dev Core Web Vitals](https://web.dev/vitals/)

### Actions concrètes

#### 1. Optimiser LCP
```typescript
// ✅ BON - Image prioritaire + dimensions explicites
<img
  src="/logo.png"
  alt="Brain RH"
  width={200}
  height={60}
  fetchpriority="high"
  decoding="async"
/>

// Preload des ressources critiques (index.html)
<link rel="preload" href="/logo.png" as="image" />
<link rel="preconnect" href="https://api.openai.com" />

// ❌ MAUVAIS - Image lazy + pas de dimensions
<img src="/logo.png" alt="Logo" loading="lazy" />
```

**Référence:** [Optimize LCP](https://web.dev/optimize-lcp/)

#### 2. Minimiser CLS
```css
/* ✅ BON - Réserver l'espace avant chargement */
.cv-card-skeleton {
  width: 100%;
  height: 200px; /* Hauteur exacte de la card finale */
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
}

@keyframes loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ❌ MAUVAIS - Pas de réservation d'espace */
.cv-card {
  /* L'élément "pousse" le contenu en dessous lors du chargement */
}
```

**Référence:** [Optimize CLS](https://web.dev/optimize-cls/)

#### 3. Code-splitting
```typescript
// ✅ BON - Lazy loading des pages non critiques
import { lazy, Suspense } from 'react';

const CVParsingPage = lazy(() => import('./pages/CVParsingPage'));
const MatchingPage = lazy(() => import('./pages/MatchingPage'));
const EnterprisesPage = lazy(() => import('./pages/EnterprisesPage'));

function App() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Routes>
        <Route path="/cvs" element={<CVParsingPage />} />
        <Route path="/matching" element={<MatchingPage />} />
        <Route path="/enterprises" element={<EnterprisesPage />} />
      </Routes>
    </Suspense>
  );
}
```

**Référence:** [Code Splitting](https://react.dev/reference/react/lazy)

#### 4. Images optimisées
```typescript
// ✅ BON - Formats modernes + responsive
<picture>
  <source srcset="/logo.avif" type="image/avif" />
  <source srcset="/logo.webp" type="image/webp" />
  <img src="/logo.png" alt="Brain RH" width={200} height={60} />
</picture>

// Ou avec un CDN d'images
<img
  src="https://cdn.example.com/logo.png?w=200&h=60&fm=avif&q=80"
  alt="Brain RH"
  width={200}
  height={60}
/>
```

---

## 📡 DATA-FETCHING & STREAMING

### 1. Fetch synchrone avec gestion d'erreur

```typescript
// api/client.ts
import axios, { AxiosError } from 'axios';

export const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types d'erreur normalisés
export interface APIError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

// Intercepteur pour normaliser les erreurs
apiClient.interceptors.response.use(
  response => response,
  (error: AxiosError<APIError>) => {
    if (error.response) {
      // Erreur du serveur (4xx, 5xx)
      throw {
        code: error.response.data.code || 'SERVER_ERROR',
        message: error.response.data.message || 'Une erreur est survenue',
        details: error.response.data.details,
        status: error.response.status
      };
    } else if (error.request) {
      // Pas de réponse (réseau)
      throw {
        code: 'NETWORK_ERROR',
        message: 'Impossible de contacter le serveur. Vérifiez votre connexion.',
        details: { originalError: error.message }
      };
    } else {
      // Erreur de configuration
      throw {
        code: 'CLIENT_ERROR',
        message: error.message,
        details: {}
      };
    }
  }
);

// Usage dans un composant
const { data, error, isLoading } = useQuery({
  queryKey: ['cvs'],
  queryFn: async () => {
    const response = await apiClient.get<CV[]>('/cvs');
    return response.data;
  },
  retry: 3,
  retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
});

if (error) {
  return <ErrorBanner code={error.code} message={error.message} />;
}
```

**Référence:** [Axios Error Handling](https://axios-http.com/docs/handling_errors), [TanStack Query](https://tanstack.com/query/latest)

### 2. Streaming SSE (Server-Sent Events)

```typescript
// hooks/useSSEStream.ts
import { useEffect, useRef, useState } from 'react';

interface SSEOptions<T> {
  url: string;
  onMessage: (data: T) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  enabled?: boolean;
}

export const useSSEStream = <T = any>({
  url,
  onMessage,
  onError,
  onOpen,
  enabled = true
}: SSEOptions<T>) => {
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!enabled) return;

    // Créer EventSource
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      onOpen?.();
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as T;
        onMessage(data);
      } catch (err) {
        console.error('Failed to parse SSE data:', err);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      setIsConnected(false);
      onError?.(error);

      // Fermer et nettoyer (auto-reconnect par défaut après 3s)
      eventSource.close();
    };

    // Cleanup
    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, [url, enabled, onMessage, onError, onOpen]);

  // Méthode pour fermer manuellement
  const close = () => {
    eventSourceRef.current?.close();
    setIsConnected(false);
  };

  return { isConnected, close };
};

// Usage dans un composant
export const CVParsingPage: React.FC = () => {
  const [progress, setProgress] = useState<ProgressEvent | null>(null);
  const [results, setResults] = useState<CVResult[]>([]);

  const { isConnected, close } = useSSEStream<SSEEvent>({
    url: 'http://localhost:8000/api/v1/cvs/parse/stream',
    enabled: parsing,
    onOpen: () => console.log('Stream connected'),
    onMessage: (event) => {
      if (event.type === 'progress') {
        setProgress(event.data);
      } else if (event.type === 'result') {
        setResults(prev => [...prev, event.data]);
      } else if (event.type === 'done') {
        close();
      }
    },
    onError: (error) => {
      console.error('Stream error:', error);
      toast.error('Connexion perdue. Reconnexion en cours...');
    }
  });

  return (
    <div>
      {isConnected && <Badge>Streaming actif</Badge>}
      {progress && <ProgressBar current={progress.current} total={progress.total} />}
      <CVResultsList results={results} />
    </div>
  );
};
```

**Spécifications SSE:**
- Content-Type: `text/event-stream`
- Header `Cache-Control: no-cache`
- Header `Connection: keep-alive`
- Format: `event: <type>\ndata: <json>\n\n`
- Reconnexion automatique après 3s (défaut navigateur)

**Référence:** [MDN EventSource](https://developer.mozilla.org/en-US/docs/Web/API/EventSource), [WHATWG SSE Spec](https://html.spec.whatwg.org/multipage/server-sent-events.html), [Web.dev Streaming](https://web.dev/articles/eventsource-basics)

### 3. Client API typé (généré depuis OpenAPI)

```bash
# Installer générateur
npm install --save-dev openapi-typescript

# Générer types TypeScript depuis openapi.yaml
npx openapi-typescript openapi.yaml -o src/types/api-schema.ts

# Ou utiliser codegen pour générer client complet
npm install --save-dev openapi-typescript-codegen
npx openapi-typescript-codegen --input openapi.yaml --output src/api/generated
```

```typescript
// Types générés automatiquement
import type { paths } from '@/types/api-schema';

// Type-safe fetcher
type ParseCVsRequest = paths['/cvs/parse']['post']['requestBody']['content']['multipart/form-data'];
type ParseCVsResponse = paths['/cvs/parse']['post']['responses']['200']['content']['application/json'];

export const parseCVs = async (files: File[]): Promise<ParseCVsResponse> => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));

  const response = await apiClient.post<ParseCVsResponse>('/cvs/parse', formData);
  return response.data;
};

// TypeScript détecte automatiquement les erreurs de typage!
```

**Avantages:**
- Zéro drift entre backend et frontend
- Autocomplétion IDE complète
- Erreurs de typage détectées à la compilation

**Référence:** [openapi-typescript](https://github.com/drwpow/openapi-typescript), [openapi-typescript-codegen](https://github.com/ferdikoomen/openapi-typescript-codegen)

---

## ♿ ACCESSIBILITÉ (WCAG 2.2 Level AA)

### 1. Contrastes de couleurs

```css
/* ✅ BON - Contraste > 4.5:1 pour texte normal */
.text-primary {
  color: #1976D2; /* Bleu foncé */
  background: #FFFFFF;
  /* Contraste: 5.2:1 ✓ */
}

/* ✅ BON - Contraste > 3:1 pour texte large (18px+) */
.heading {
  font-size: 24px;
  color: #2196F3; /* Bleu moyen */
  background: #FFFFFF;
  /* Contraste: 3.1:1 ✓ */
}

/* ❌ MAUVAIS - Contraste insuffisant */
.text-light {
  color: #BBDEFB; /* Bleu clair */
  background: #FFFFFF;
  /* Contraste: 1.8:1 ✗ */
}
```

**Outil:** [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

### 2. Navigation clavier

```typescript
// ✅ BON - Composant accessible (Radix/shadcn)
import { Dialog, DialogContent, DialogTrigger } from '@/components/ui/dialog';

<Dialog>
  <DialogTrigger asChild>
    <Button>Ouvrir les détails</Button>
  </DialogTrigger>
  <DialogContent>
    {/* Focus automatiquement piégé dans la modale */}
    {/* Fermeture avec Escape */}
    {/* Navigation Tab entre contrôles */}
    <CVDetails cv={selectedCV} />
  </DialogContent>
</Dialog>

// ❌ MAUVAIS - Modale custom sans gestion focus
<div className="modal" onClick={closeModal}>
  <div onClick={(e) => e.stopPropagation()}>
    {/* Pas de piège focus, Tab sort de la modale */}
    {/* Escape ne ferme pas */}
    <CVDetails cv={selectedCV} />
  </div>
</div>
```

**Référence:** [Radix Dialog](https://www.radix-ui.com/primitives/docs/components/dialog), [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)

### 3. Labels et ARIA

```typescript
// ✅ BON - Label associé, rôles ARIA corrects
<div role="group" aria-labelledby="classification-heading">
  <h3 id="classification-heading">Classification des critères</h3>

  {criteres.map(critere => (
    <div key={critere.id}>
      <Label htmlFor={`classification-${critere.id}`}>
        {critere.text}
      </Label>
      <Select id={`classification-${critere.id}`} aria-required="true">
        <SelectItem value="must-have">Must-have</SelectItem>
        <SelectItem value="nice-to-have">Nice-to-have</SelectItem>
      </Select>
    </div>
  ))}
</div>

// ❌ MAUVAIS - Pas de label, pas d'association
<div>
  <h3>Classification</h3>
  {criteres.map(critere => (
    <div>
      <span>{critere.text}</span>
      <select> {/* Pas de label associé, lecteur d'écran ne peut pas annoncer */}
        <option>Must-have</option>
      </select>
    </div>
  ))}
</div>
```

### 4. Tailles de cibles tactiles

```css
/* ✅ BON - Cible > 44x44px (WCAG 2.2 Level AA) */
.button {
  min-width: 44px;
  min-height: 44px;
  padding: 12px 24px;
}

.icon-button {
  width: 48px;
  height: 48px;
}

/* ❌ MAUVAIS - Cible trop petite */
.tiny-button {
  width: 24px;
  height: 24px;
}
```

**Référence:** [WCAG 2.2 Target Size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)

---

## 🧪 TESTS (Peu, mais bien placés)

### 1. Tests composants (Testing Library)

```typescript
// CVUploader.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CVUploader } from './CVUploader';

describe('CVUploader', () => {
  it('should call onFilesSelected when files are dropped', async () => {
    const onFilesSelected = jest.fn();
    render(<CVUploader onFilesSelected={onFilesSelected} />);

    const file = new File(['content'], 'cv.pdf', { type: 'application/pdf' });
    const input = screen.getByLabelText(/glissez.*déposez/i);

    await userEvent.upload(input, file);

    expect(onFilesSelected).toHaveBeenCalledWith([file]);
  });

  it('should display error for invalid file type', async () => {
    const onFilesSelected = jest.fn();
    render(<CVUploader onFilesSelected={onFilesSelected} />);

    const file = new File(['content'], 'cv.txt', { type: 'text/plain' });
    const input = screen.getByLabelText(/glissez.*déposez/i);

    await userEvent.upload(input, file);

    expect(screen.getByText(/type de fichier invalide/i)).toBeInTheDocument();
    expect(onFilesSelected).not.toHaveBeenCalled();
  });

  it('should be disabled when parsing', () => {
    render(<CVUploader onFilesSelected={jest.fn()} disabled />);

    const input = screen.getByLabelText(/glissez.*déposez/i);
    expect(input).toBeDisabled();
  });
});
```

**Règles Testing Library:**
- Sélectionner par rôle/label/texte (comme un utilisateur)
- Éviter `data-testid` sauf si nécessaire
- Pas de tests d'implémentation (state interne, props)

**Référence:** [Testing Library Best Practices](https://testing-library.com/docs/guiding-principles/)

### 2. Tests E2E (Playwright)

```typescript
// e2e/cv-parsing.spec.ts
import { test, expect } from '@playwright/test';

test.describe('CV Parsing Flow', () => {
  test('should parse CVs successfully', async ({ page }) => {
    // Navigation
    await page.goto('http://localhost:5173/cvs');

    // Upload fichier
    await page.setInputFiles('input[type="file"]', [
      'fixtures/cv1.pdf',
      'fixtures/cv2.pdf'
    ]);

    // Lancer parsing
    await page.click('button:has-text("Analyser les CVs")');

    // Attendre résultats
    await expect(page.locator('text=2 CVs parsés avec succès')).toBeVisible({ timeout: 60000 });

    // Vérifier liste
    const results = page.locator('[data-testid="cv-result"]');
    await expect(results).toHaveCount(2);
  });

  test('should handle parsing errors gracefully', async ({ page }) => {
    await page.goto('http://localhost:5173/cvs');

    await page.setInputFiles('input[type="file"]', ['fixtures/corrupted.pdf']);
    await page.click('button:has-text("Analyser")');

    await expect(page.locator('text=/impossible.*parser/i')).toBeVisible();
  });
});
```

**Référence:** [Playwright Best Practices](https://playwright.dev/docs/best-practices)

---

## ✅ CHECKLIST "DEFINITION OF DONE" (DoD)

Avant chaque merge/déploiement, vérifier:

### Accessibilité
- [ ] Navigation clavier complète (Tab, Shift+Tab, Enter, Escape)
- [ ] Focus visible sur tous les contrôles interactifs
- [ ] Labels associés à tous les inputs (`htmlFor` / `aria-label`)
- [ ] Contrastes de couleurs > 4.5:1 (texte normal) ou > 3:1 (texte large)
- [ ] Tailles de cibles tactiles > 44x44px
- [ ] Composants Radix/shadcn utilisés pour modales/menus/listes

**Outil de validation:** [axe DevTools](https://www.deque.com/axe/devtools/)

### Performance
- [ ] LCP < 2.5s sur page cible (Lighthouse en mode dev)
- [ ] CLS < 0.1 (pas de décalages visuels)
- [ ] INP < 200ms (interactions fluides)
- [ ] Code-splitting activé pour pages lourdes (lazy loading)
- [ ] Images optimisées (WebP/AVIF + dimensions explicites)

**Outil de validation:** [Lighthouse](https://developer.chrome.com/docs/lighthouse/), [WebPageTest](https://www.webpagetest.org/)

### Code & État
- [ ] Aucun `useEffect` inutile (calculer au lieu de synchroniser)
- [ ] État minimal (pas de doublons, dérivés calculés à la volée)
- [ ] Logique extraite dans hooks custom (composants purs UI)
- [ ] Types TypeScript stricts (pas de `any`, interfaces complètes)

### Streaming SSE (si applicable)
- [ ] EventSource gère `onopen`, `onmessage`, `onerror`
- [ ] Fermeture propre (`close()`) au démontage du composant
- [ ] Serveur renvoie `Content-Type: text/event-stream`
- [ ] Reconnexion automatique testée (coupure réseau simulée)

### API & Erreurs
- [ ] Appels API typés (types générés depuis OpenAPI)
- [ ] Erreurs normalisées `{code, message, details}` affichées proprement
- [ ] Retry automatique sur erreurs réseau (3 tentatives + backoff)
- [ ] Toast/inline errors pour feedback utilisateur

### Tests
- [ ] Au moins 1 test DOM (Testing Library) par composant critique
- [ ] Au moins 1 parcours E2E (Playwright) sur page P0
- [ ] Tests de régression pour logique métier (scores, formules)

---

## 📚 RÉFÉRENCES OFFICIELLES

### React & TypeScript
- [React Documentation](https://react.dev/)
- [You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

### Design System & UI
- [shadcn/ui](https://ui.shadcn.com/)
- [Radix UI](https://www.radix-ui.com/)
- [Material Design 3](https://m3.material.io/)
- [Carbon Design System](https://carbondesignsystem.com/)

### Accessibilité
- [WCAG 2.2 Guidelines](https://www.w3.org/WAI/WCAG22/quickref/)
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

### Performance
- [Web.dev Core Web Vitals](https://web.dev/vitals/)
- [Optimize LCP](https://web.dev/optimize-lcp/)
- [Optimize CLS](https://web.dev/optimize-cls/)

### Streaming & API
- [MDN EventSource](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
- [WHATWG SSE Spec](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [TanStack Query](https://tanstack.com/query/latest)
- [openapi-typescript](https://github.com/drwpow/openapi-typescript)

### Tests
- [Testing Library](https://testing-library.com/docs/guiding-principles/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)

---

**Ce document doit être appliqué dès le Palier 3 (frontend).** Chaque composant, chaque page doit respecter ces standards pour garantir une application professionnelle, accessible et performante.
