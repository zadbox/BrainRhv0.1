# 📋 Méthodologie de Test Systématique

## Vue d'ensemble

Cette méthodologie garantit que **chaque action utilisateur** est tracée de bout en bout avec des **preuves à chaque étape**.

### Stack Technique
- **Frontend**: React 18 + TypeScript + React Router + Axios
- **Backend**: FastAPI + Python 3.9
- **Communication**: REST + SSE (Server-Sent Events)
- **Storage**: Filesystem (JSON)

---

## 🔍 Checklist des 8 Étapes Obligatoires

Pour chaque action testée, fournir les preuves suivantes :

### 1. [UI] Handler câblé au clic
**Preuve attendue**: Code du composant montrant le `onClick` + log console

```typescript
// Exemple
<Button onClick={() => {
  console.log('[UI] Click: Lancer matching');
  handleRunMatching();
}}>
  Lancer le matching
</Button>
```

### 2. [HTTP/SSE] Requête vers la bonne ressource
**Preuve attendue**: Capture Network OU log de `fetchWithTrace`

```
[REQ a1b2c3d4] POST http://localhost:8000/api/v1/matching/run/stream?project_id=xxx
📤 Request ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
🔗 URL: http://localhost:8000/api/v1/matching/run/stream?project_id=banque-de-france&runId=abc123
⚙️  Init: { method: 'POST', body: {...} }
```

### 3. [FastAPI] Bonne route exécutée
**Preuve attendue**: Log serveur avec request ID + status

```
[API][a1b2c3d4] → POST /api/v1/matching/run/stream?project_id=banque-de-france&runId=abc123
[API][a1b2c3d4]   body: {"top_n_rerank":10,"model":"gpt-5-mini"}
[API][a1b2c3d4] ← 200 (15234ms)
```

### 4. [Contrat] JSON validé
**Preuve attendue**: Zod parse OU types TypeScript générés

```typescript
const MatchingResultSchema = z.object({
  results: z.array(z.object({
    cv: z.string(),
    score_final: z.number(),
    commentaire_scoring: z.string(),
  })),
  metadata: z.object({
    total_cvs: z.number(),
    top_reranked: z.number(),
  }),
});

// Validation
const validated = MatchingResultSchema.parse(data); // ✅ OK
```

### 5. [State] Donnée stockée
**Preuve attendue**: Ligne de code du setter + clé exacte

```typescript
// Exemple avec React Query
queryClient.setQueryData(['matching', projectId, matchingId], data);

// OU Zustand
store.setMatchingResult(projectId, matchingId, data);
```

### 6. [Select] Composant lit la bonne donnée
**Preuve attendue**: Sélecteur + props reçues

```typescript
// Hook
const { data: matchingResult } = useQuery(['matching', projectId, matchingId]);

// Composant
<ResultsTable results={matchingResult.results} />
```

### 7. [UI] Affichage final correct
**Preuve attendue**: Assertion Playwright OU screenshot

```typescript
// Playwright
await expect(page.getByRole('row')).toHaveCount(11); // header + 10 results
await expect(page.getByText('Score: 0.85')).toBeVisible();
```

### 8. [SSE] Une seule connexion, fermeture propre
**Preuve attendue**: Logs SSE + Network

```
[SSE a1b2c3d4] 🔌 Opening connection to /api/v1/matching/run/stream?...
[SSE a1b2c3d4] ✅ Connected (234ms)
[SSE a1b2c3d4] 📨 progress: {"stage":"filtering","progress":30}
[SSE a1b2c3d4] 📨 done: {"status":"success"}
[SSE a1b2c3d4] 🔌 Connection closed (15234ms)
```

---

## 📦 Routes API du Projet

### Entreprises
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/enterprises` | GET | Liste entreprises |
| `/api/v1/enterprises` | POST | Créer entreprise |
| `/api/v1/enterprises/{id}` | GET | Détails entreprise |

### Projets
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/projects` | GET | Liste projets (filtrable par `enterprise_id`) |
| `/api/v1/projects` | POST | Créer projet (requiert `enterprise_id`) |
| `/api/v1/projects/{id}` | GET | Détails projet |
| `/api/v1/projects/{id}/history` | GET | Historique matchings |
| `/api/v1/projects/{id}/matchings/latest` | GET | Dernier matching |

### Matching
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/matching/run/stream` | GET (SSE) | Lancer matching en streaming |
| `/api/v1/matching/results/{project_id}/{timestamp}` | GET | Résultats d'un matching |

### CVs
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/cvs/{project_id}` | GET | Liste CVs d'un projet |
| `/api/v1/cvs/{project_id}` | POST | Upload CV |

### Offres
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/offres/{project_id}` | GET | Offre d'un projet |
| `/api/v1/offres/{project_id}` | POST | Créer/Mettre à jour offre |

---

## 🎯 Scénarios de Test Types

### Scénario 1: Lancer un Matching

**Action**: Clic sur "Lancer le matching" dans ProjectDetailPage

**Checklist**:
1. ✅ Handler: `ProjectDetailPage.tsx:202` → `onClick={() => navigate('/matching')}`
2. ✅ HTTP: `GET /api/v1/matching/run/stream?project_id=xxx&runId=yyy` (SSE)
3. ✅ Backend: Route `matching.py:run_matching_stream` exécutée
4. ✅ Contrat: Stream de `ProgressEvent` + `DoneEvent` validés par Zod
5. ✅ State: `useMatchingStore().setCurrentRun(runId, events)`
6. ✅ Select: `<MatchingProgress runId={runId} />` lit `store.runs[runId]`
7. ✅ UI: Barre de progression 0→100%, puis tableau de 10 résultats
8. ✅ SSE: Une connexion, close sur event `done`

### Scénario 2: Voir l'Historique des Matchings

**Action**: Clic sur "Voir les résultats" dans ProjectDetailPage

**Checklist**:
1. ✅ Handler: `ProjectDetailPage.tsx:221` → `onClick={() => navigate('/results')}`
2. ✅ HTTP: `GET /api/v1/projects/{project_id}/history`
3. ✅ Backend: Route `projects.py:get_project_history` exécutée
4. ✅ Contrat: `ProjectHistory` validé (total, items[])
5. ✅ State: React Query cache `['project-history', projectId]`
6. ✅ Select: `useQuery(['project-history', projectId])`
7. ✅ UI: Tableau avec timestamps, nombre de candidats, filtre par date
8. ✅ N/A (pas de SSE)

### Scénario 3: Filtrer Projets par Entreprise

**Action**: Sélection d'une entreprise dans le dropdown EnterprisesPage

**Checklist**:
1. ✅ Handler: `EnterprisesPage.tsx:45` → `onChange={(e) => setFilter(e.target.value)}`
2. ✅ HTTP: `GET /api/v1/projects?enterprise_id=projets-existants`
3. ✅ Backend: Route `projects.py:list_projects` avec query param
4. ✅ Contrat: `Project[]` validé
5. ✅ State: React Query cache `['projects', { enterpriseId }]`
6. ✅ Select: `useQuery(['projects', { enterpriseId: filter }])`
7. ✅ UI: Liste de projets filtrée, badge avec nombre
8. ✅ N/A (pas de SSE)

---

## 🛠️ Outils d'Infrastructure

### Backend - Middleware Logging
**Fichier**: `api/middleware/logging_middleware.py`

**Usage**:
```python
# api/main.py
from api.middleware import LoggingMiddleware

app.add_middleware(LoggingMiddleware)
```

**Output exemple**:
```
[API][a1b2c3d4] → GET /api/v1/projects?enterprise_id=xxx
[API][a1b2c3d4] ← 200 (45ms)
```

### Frontend - Fetch avec Trace
**Fichier**: `frontend/src/lib/fetchWithTrace.ts`

**Usage**:
```typescript
import { fetchWithTrace } from '@/lib/fetchWithTrace';

const { data, requestId } = await fetchWithTrace('/api/v1/projects');
```

**Output console**:
```
[REQ a1b2c3d4] GET http://localhost:8000/api/v1/projects
📤 Request ID: a1b2c3d4-...
✅ Status: 200 OK
📦 Data: [{...}, ...]
```

### Frontend - EventSource avec Trace
**Usage**:
```typescript
import { EventSourceWithTrace } from '@/lib/fetchWithTrace';

const es = new EventSourceWithTrace('/api/v1/matching/run/stream?...');
es.addEventListener('progress', (e) => {
  es.logMessage('progress', JSON.parse(e.data));
});
```

---

## ✅ Template de Test à Copier-Coller

```markdown
## Test: [Nom de l'action]

**Action**: [Description de ce que fait l'utilisateur]

### Checklist des Preuves

1. **[UI] Handler câblé**
   - [ ] Fichier: `xxx.tsx:ligne`
   - [ ] Code: `onClick={() => ...}`
   - [ ] Log: `[UI] Click: ...`

2. **[HTTP/SSE] Requête correcte**
   - [ ] Méthode: GET/POST
   - [ ] URL: `/api/v1/...`
   - [ ] Params/Body: `{...}`
   - [ ] Request ID: `abc123...`

3. **[FastAPI] Route exécutée**
   - [ ] Fichier: `api/routers/xxx.py:ligne`
   - [ ] Fonction: `async def xxx(...)`
   - [ ] Log: `[API][abc123] → ... ← 200`

4. **[Contrat] Validation**
   - [ ] Schema: `XxxSchema = z.object({...})`
   - [ ] Validation: `parse(data)` OK
   - [ ] Champs clés présents: `[...]`

5. **[State] Stockage**
   - [ ] Hook/Store: `useQuery / useState / Zustand`
   - [ ] Clé: `['xxx', id]` ou `store.xxx[id]`
   - [ ] Setter: `setQueryData / setState`

6. **[Select] Lecture**
   - [ ] Sélecteur: `useQuery(['xxx', id])`
   - [ ] Props: `<Component data={xxx} />`

7. **[UI] Affichage**
   - [ ] Assertion: `expect(...).toHaveCount(N)`
   - [ ] Screenshot: [lien ou embed]
   - [ ] Colonnes/Champs: `[...]`

8. **[SSE] Connexion unique** (si applicable)
   - [ ] Log: `[SSE] open → messages → close`
   - [ ] Network: 1 connexion active
   - [ ] Fermeture: sur event `done`

### Résultat
- ✅ Tous les tests passés
- ❌ Échec à l'étape X: [description]
```

---

## 📊 Rapport de Test Exemple

### Test: Lancer un Matching

| Étape | Statut | Preuve |
|-------|--------|--------|
| 1. UI Handler | ✅ | `ProjectDetailPage.tsx:202` |
| 2. HTTP Request | ✅ | `[REQ a1b2c3d4] GET /matching/run/stream` |
| 3. Backend Route | ✅ | `[API][a1b2c3d4] → GET /matching/run/stream ← 200` |
| 4. Contrat | ✅ | Zod parse OK, 10 results |
| 5. State | ✅ | `store.runs[runId] = {...}` |
| 6. Select | ✅ | `useMatchingStore().runs[runId]` |
| 7. UI Display | ✅ | 10 rows visible, scores formatted |
| 8. SSE | ✅ | 1 connexion, close après done |

**Résultat final**: ✅ **8/8 tests passés**

---

## 🚨 Règle d'Or

**Chaque étape = 1 preuve**. Pas de "ça marche chez moi" sans artefact.

Si une étape échoue, **arrêter immédiatement** et corriger avant de continuer.
