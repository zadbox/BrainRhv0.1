# PALIER 3 - PLAN D'IMPLÉMENTATION FRONTEND

**Date:** 11 octobre 2025
**Objectif:** Frontend React complet avec 100% de parité fonctionnelle avec l'API

---

## 🎯 STRUCTURE CIBLE

```
frontend/
├── public/
│   └── logo.png
├── src/
│   ├── app/
│   │   ├── main.tsx              # Entry point
│   │   ├── router.tsx            # Routes
│   │   └── App.tsx               # App principal
│   │
│   ├── components/
│   │   ├── ui/                   # Components shadcn (Button, Card, etc.)
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── input.tsx
│   │   │   ├── label.tsx
│   │   │   ├── select.tsx
│   │   │   ├── table.tsx
│   │   │   ├── progress.tsx
│   │   │   └── toast.tsx
│   │   │
│   │   ├── layout/
│   │   │   ├── Header.tsx        # Header avec logo + theme toggle
│   │   │   ├── Sidebar.tsx       # Sidebar collapsible
│   │   │   └── Layout.tsx        # Layout global
│   │   │
│   │   └── shared/
│   │       ├── Loading.tsx
│   │       ├── ErrorBanner.tsx
│   │       └── EmptyState.tsx
│   │
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── EnterprisesPage.tsx   # P0: CRUD Entreprises
│   │   ├── ProjectsPage.tsx      # P0: CRUD Projets
│   │   ├── CVBasePage.tsx        # P0: Base CVs
│   │   ├── CVParsingPage.tsx     # P1: Parsing avec SSE
│   │   ├── MatchingPage.tsx      # P1: Matching avec SSE
│   │   └── ResultsPage.tsx       # P1: Résultats + exports
│   │
│   ├── hooks/
│   │   ├── useTheme.ts           # Dark mode
│   │   ├── useSSE.ts             # SSE générique
│   │   ├── useEnterprises.ts
│   │   ├── useProjects.ts
│   │   ├── useCVs.ts
│   │   └── useMatching.ts
│   │
│   ├── stores/
│   │   ├── useThemeStore.ts      # Zustand theme
│   │   └── useAppStore.ts        # State global
│   │
│   ├── api/
│   │   ├── client.ts             # Axios config
│   │   ├── enterprises.ts
│   │   ├── projects.ts
│   │   ├── cvs.ts
│   │   ├── matching.ts
│   │   └── types.ts              # Types API
│   │
│   ├── lib/
│   │   └── utils.ts              # Utilitaires (cn, etc.)
│   │
│   ├── index.css                 # Styles globaux + Tailwind
│   └── vite-env.d.ts
│
├── index.html
├── package.json
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
├── tsconfig.node.json
└── vite.config.ts
```

---

## 📝 ORDRE D'IMPLÉMENTATION

### Phase 1: Fondations ✅
1. ✅ Setup Vite + React + TypeScript
2. ✅ Configuration Tailwind CSS
3. ✅ CSS Variables pour dark mode

### Phase 2: Infrastructure (EN COURS)
4. ⏳ Utils (lib/utils.ts avec fonction `cn`)
5. ⏳ Client API (axios + types)
6. ⏳ Stores Zustand (theme + app)
7. ⏳ Hooks custom

### Phase 3: Composants UI (shadcn/ui)
8. ⏳ Composants de base (Button, Card, Input, etc.)
9. ⏳ Components layout (Header, Sidebar, Layout)
10. ⏳ Components shared (Loading, Error, EmptyState)

### Phase 4: Pages P0 (Priorité haute)
11. ⏳ **EnterprisesPage** (CRUD complet)
12. ⏳ **ProjectsPage** (CRUD + historique)
13. ⏳ **CVBasePage** (liste + upload)

### Phase 5: Pages P1 (Fonctionnalités core)
14. ⏳ **CVParsingPage** (SSE streaming)
15. ⏳ **MatchingPage** (SSE + configuration)
16. ⏳ **ResultsPage** (scorecard + exports)

### Phase 6: Polish & Tests
17. ⏳ HomePage (dashboard)
18. ⏳ Router (toutes les routes)
19. ⏳ Tests finaux
20. ⏳ Vérifications (accessibilité, performance, dark mode)

---

## 🔧 DÉTAILS TECHNIQUES

### Dark Mode

**Implémentation:**
- Zustand pour state management
- CSS Variables (HSL) pour les couleurs
- classe `.dark` sur `<html>`
- Toggle dans Header
- Persistance localStorage
- Support `prefers-color-scheme`

**Fichiers:**
- `stores/useThemeStore.ts`
- `hooks/useTheme.ts`
- `components/layout/Header.tsx` (toggle)

### Sidebar Collapsible

**Comportement:**
- Desktop: Sidebar fixe (240px) avec bouton collapse
- Collapsed: Icônes uniquement (64px)
- Mobile: Drawer avec overlay
- État persisté dans localStorage

**Ordre menu (demandé par user):**
1. 🏢 Entreprises
2. 📁 Projets
3. 📄 Base CVs
4. 🔄 Parsing CVs
5. 🎯 Matching
6. 📊 Résultats

### API Client

**Configuration:**
```typescript
// api/client.ts
export const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 300000, // 5 min (LLM calls)
  headers: {
    'Content-Type': 'application/json',
  },
});
```

**Gestion d'erreurs:**
- Intercepteur axios
- Normalisation format `{code, message, details}`
- Toast pour affichage

### SSE Streaming

**Hook générique:**
```typescript
// hooks/useSSE.ts
export const useSSE = <T>(url: string, enabled: boolean) => {
  const [events, setEvents] = useState<T[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!enabled) return;

    const eventSource = new EventSource(url);

    eventSource.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [...prev, data]);
    };

    eventSource.onerror = () => {
      eventSource.close();
      setIsConnected(false);
    };

    return () => eventSource.close();
  }, [url, enabled]);

  return { events, isConnected };
};
```

---

## 📄 PAGES DÉTAILLÉES

### 1. EnterprisesPage

**Fonctionnalités:**
- Liste des entreprises (table)
- Bouton "Nouvelle entreprise" (dialog)
- Edit inline (dialog)
- Delete avec confirmation
- Filtres/recherche

**Composants:**
- Table (shadcn)
- Dialog (shadcn) pour create/edit
- AlertDialog (shadcn) pour delete

**API:**
- GET `/enterprises` → liste
- POST `/enterprises` → create
- PUT `/enterprises/{id}` → update
- DELETE `/enterprises/{id}` → delete

### 2. ProjectsPage

**Fonctionnalités:**
- Liste des projets (cards)
- Sélection entreprise (select)
- Création projet (dialog)
- Edit projet (dialog)
- Voir historique (table matchings)
- Navigation vers CVs/Matching

**Composants:**
- Cards (shadcn)
- Select (shadcn) pour entreprises
- Dialog pour CRUD
- Table pour historique

**API:**
- GET `/projects` → liste (avec filter enterprise_id)
- POST `/projects` → create
- PUT `/projects/{id}` → update
- DELETE `/projects/{id}` → delete (soft)
- GET `/projects/{id}/history` → historique

### 3. CVBasePage

**Fonctionnalités:**
- Upload CVs (drag & drop)
- Liste CVs parsés du projet
- Bouton "Parser" → navigate to CVParsingPage
- Delete CV
- Recherche/filtre

**Composants:**
- FileUpload (custom)
- Cards pour CVs
- Button "Parser maintenant"

**API:**
- Upload temporaire (stockage côté serveur TODO)
- Liste depuis projet (TODO: endpoint manquant)

### 4. CVParsingPage

**Fonctionnalités:**
- Upload fichiers
- SSE streaming progress
- Liste résultats temps-réel
- Succès/échecs
- Temps écoulé

**Composants:**
- Progress (shadcn)
- Cards pour résultats
- SSE avec `useSSE` hook

**API:**
- POST `/cvs/parse/stream` (SSE)

### 5. MatchingPage

**Fonctionnalités:**
- Sélection projet
- Chargement offre projet
- Chargement CVs projet
- Configuration (top_n_rerank, model)
- Lancement matching (SSE)
- 4 étapes (progress bars)
- Résultats intermédiaires

**Composants:**
- Select projet
- Form configuration
- Progress multi-étapes
- SSE streaming

**API:**
- GET `/offres/{project_id}/offre` → offre
- GET CVs projet (TODO)
- POST `/matching/run/stream` (SSE)

### 6. ResultsPage

**Fonctionnalités:**
- Scorecard (top 10 CVs)
- Détails par CV (scores, commentaires)
- Exports (CSV, JSON)
- Filtres (score min, nice-have)

**Composants:**
- Table (shadcn) avec sorting
- Dialog détails CV
- Buttons export

**API:**
- GET `/matching/{project_id}/{timestamp}/results`
- GET `/matching/{project_id}/{timestamp}/export/csv`
- GET `/matching/{project_id}/{timestamp}/export/json`

---

## ✅ CHECKLIST FINALE

### Fonctionnalités
- [ ] CRUD Entreprises complet
- [ ] CRUD Projets complet
- [ ] Upload CVs + liste
- [ ] Parsing CVs avec SSE
- [ ] Matching avec SSE (4 étapes)
- [ ] Résultats + exports

### Dark Mode
- [ ] Toggle dans Header
- [ ] Persistance localStorage
- [ ] Toutes les pages fonctionnent en dark
- [ ] Transitions fluides
- [ ] Contrastes WCAG AA

### Sidebar
- [ ] Collapsible (icônes uniquement)
- [ ] Ordre: Entreprises → Projets → CVs → Parsing → Matching → Résultats
- [ ] Responsive (drawer sur mobile)
- [ ] Persistance état (localStorage)

### Accessibilité
- [ ] Navigation clavier complète
- [ ] Focus visible
- [ ] Labels sur tous les inputs
- [ ] Contrastes > 4.5:1
- [ ] Composants Radix (accessible)

### Performance
- [ ] LCP < 2.5s
- [ ] Code splitting (lazy pages)
- [ ] Pas de useEffect inutiles
- [ ] État minimal

### API
- [ ] Toutes les pages connectées
- [ ] Gestion d'erreurs complète
- [ ] SSE fonctionnel
- [ ] Toast pour feedback

---

## 🚀 ESTIMATION

**Temps total:** 6-8 heures de développement intensif

**Breakdown:**
- Infrastructure (utils, stores, hooks): 1h
- Composants UI (shadcn): 1h
- Layout + dark mode: 1h
- Pages P0 (Entreprises, Projets, CVs): 2h
- Pages P1 (Parsing, Matching, Résultats): 2-3h
- Tests + polish: 1h

**Prêt à démarrer l'implémentation complète maintenant !**
