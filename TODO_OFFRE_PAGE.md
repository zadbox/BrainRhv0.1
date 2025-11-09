# TODO: Refonte complète OffrePage pour conformité Streamlit

## Problèmes identifiés

### 1. ❌ Pas de parsing d'offre
**Streamlit:** Upload PDF/DOCX ou texte → Bouton "Préparer l'offre" → GPT-5 mini parse → JSON structuré
**React actuel:** Formulaire manuel avec champs séparés

### 2. ❌ Sélections enrichissement pas appliquées correctement
**Problème:** Les outils/langages vont dans `sections.outils` et `sections.langages`, pas `competences_techniques`
**Code backend:** `merge_enrichment()` dans `offer_enrichment.py` lignes 240-330

### 3. ❌ Structure modèle Pydantic incomplète
**Manquant:** Champs `outils` et `langages` dans `OffreSection`

## Solutions proposées

### Backend ✅ FAIT

1. ✅ Ajout endpoint `POST /{project_id}/parse` (texte → JSON)
2. ✅ Ajout endpoint `POST /{project_id}/parse/file` (PDF/DOCX → JSON)
3. ⚠️ **À FAIRE:** Ajouter champs `outils` et `langages` dans `lib/models.py`
4. ⚠️ **À FAIRE:** Créer endpoint `POST /{project_id}/apply` qui appelle `merge_enrichment()` du backend

### Frontend - Option A: Refonte complète (fidèle Streamlit)

**Structure:**
```
┌─────────────────────────────────────────────────┐
│ Header (Projet / Offre)                   [Save]│
├─────────────────────────────────────────────────┤
│ ┌────────────────┐ ┌────────────────────────┐   │
│ │ Col 1 (Input)  │ │ Col 2 (Aperçu + Enrich)│   │
│ │                │ │                        │   │
│ │ [Upload/Texte] │ │ JSON Viewer            │   │
│ │                │ │                        │   │
│ │ [Préparer]     │ │ [Card: ROME]           │   │
│ │                │ │ [Card: IA]             │   │
│ └────────────────┘ └────────────────────────┘   │
├─────────────────────────────────────────────────┤
│ [Card: Propositions enrichissement (si actif)]  │
│ - Compétences (checkboxes)                      │
│ - Outils (checkboxes)                           │
│ - Langages (checkboxes)                         │
│ - Certifications (checkboxes)                   │
│ - Missions (checkboxes)                         │
│ - Questions (inputs)                            │
│                                                  │
│ [Bouton: Appliquer les sélections]              │
└─────────────────────────────────────────────────┘
```

**Workflow:**
1. User upload PDF/DOCX OU colle texte
2. Clic "Préparer l'offre" → API `POST /parse` ou `/parse/file`
3. Affichage JSON dans viewer (col 2)
4. User peut enrichir avec ROME ou IA
5. Propositions affichées en bas avec checkboxes
6. Clic "Appliquer" → API `POST /apply` → Fusionne dans JSON
7. JSON mis à jour dans viewer
8. Bouton "Sauvegarder" → `POST /offre` → Sauvegarde finale

### Frontend - Option B: Hybride (actuel + parsing)

Garder le formulaire actuel mais ajouter :
- Onglet "Upload/Texte" pour parsing initial
- Bouton "Parser l'offre" qui remplit le formulaire
- Corriger la logique `applySelections()` pour respecter la structure backend

## Recommandation

**Option A** est plus fidèle à Streamlit et évite la duplication formulaire/JSON.
**Option B** est plus rapide à implémenter mais moins cohérent.

**Je recommande Option A** pour une parité complète avec Streamlit.

## Fichiers à modifier (Option A)

### Backend
- [x] `api/routers/offres.py` - Endpoints parse/parse_file ajoutés
- [ ] `lib/models.py` - Ajouter `outils: List[str]` et `langages: List[str]` dans `OffreSection`
- [ ] `api/routers/offres.py` - Endpoint `POST /{project_id}/apply` qui appelle `merge_enrichment()`

### Frontend
- [ ] `frontend/src/api/offres.ts` - Ajouter méthodes `parseText()`, `parseFile()`, `applyEnrichment()`
- [ ] `frontend/src/pages/OffrePage.tsx` - Refonte complète avec nouveau layout
- [ ] `frontend/src/components/` - Créer `JsonViewer.tsx` pour affichage JSON interactif

## Estimation
- Backend: 1h (ajouter champs modèle + endpoint apply)
- Frontend: 3-4h (refonte complète page)

**Total: 4-5h de développement**
