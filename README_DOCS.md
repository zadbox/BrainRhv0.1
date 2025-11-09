# 📚 DOCUMENTATION POUR CLAUDE CODE

**Objectif:** Guider Claude pour une efficacité maximale sur ce projet

---

## 🎯 WORKFLOW OBLIGATOIRE

### Pour TOUTE tâche de code, suivre CET ORDRE :

```
┌─────────────────────────────────────────────┐
│  1. Lire REFERENCE_COMPLETE.md              │
│     → "Où est le code ?"                    │
│     → Localiser fichier:lignes exacts       │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  2. Lire CODING_RULES.md                    │
│     → "Comment modifier ce code ?"          │
│     → Appliquer les patterns obligatoires  │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  3. Modifier le code                        │
│     → Suivre les patterns                   │
│     → Vérifier la checklist                 │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  4. Mettre à jour les docs si nécessaire    │
│     → Lire MAINTENANCE_GUIDE.md             │
│     → MAJ REFERENCE ou CODING_RULES         │
└─────────────────────────────────────────────┘
```

---

## 📖 LES 3 FICHIERS ESSENTIELS

### 1. REFERENCE_COMPLETE.md ⭐ (TOUJOURS LIRE EN PREMIER)

**Usage:** Carte du projet
**Quand:** Avant CHAQUE tâche de code
**Contenu:**
- Structure fichiers/dossiers
- Mapping fonctionnalité → fichier:ligne
- Routes API
- Schemas
- Commandes utiles
- Diagnostics erreurs

**Exemple:**
```
Q: "Où est le code de filtrage must-have ?"
A: Lire REFERENCE_COMPLETE.md → Section "Filtrage Must-have"
   → matching_engine.py:450-580
```

---

### 2. CODING_RULES.md ⭐ (LIRE AVANT D'ÉCRIRE DU CODE)

**Usage:** Règles & patterns obligatoires
**Quand:** Avant d'écrire/modifier du code
**Contenu:**
- 6 règles critiques (chemins, SSE, imports, config, schemas, parallélisation)
- 3 patterns obligatoires (routes API, SSE, chargement données)
- Exemples ❌ AVANT / ✅ APRÈS
- Checklist avant commit

**Exemple:**
```
Q: "Comment accéder aux fichiers d'un projet ?"
A: Lire CODING_RULES.md → Section "Règle 1"
   → Utiliser pm.get_project_path(project_id)
   → JAMAIS Path("projects") / project_id
```

---

### 3. MAINTENANCE_GUIDE.md (LIRE APRÈS MODIFICATION)

**Usage:** Comment maintenir les docs à jour
**Quand:** Après avoir fait une modification significative
**Contenu:**
- Quand mettre à jour REFERENCE ou CODING_RULES
- Comment mettre à jour
- Exemples de mises à jour
- Checklist de maintenance

**Exemple:**
```
Q: "J'ai ajouté une nouvelle route API, que faire ?"
A: Lire MAINTENANCE_GUIDE.md → Section "Quand mettre à jour"
   → MAJ REFERENCE_COMPLETE.md section "API REST"
   → Ajouter ligne dans tableau "Endpoints disponibles"
```

---

## ⚡ QUICK START (POUR CLAUDE)

### Nouvelle tâche de code

1. **Lire REFERENCE_COMPLETE.md**
   - Trouver où est le code concerné
   - Noter fichier:lignes exacts

2. **Lire CODING_RULES.md**
   - Identifier les règles applicables
   - Mémoriser les patterns

3. **Lire le code source**
   - Aller directement aux lignes identifiées
   - Comprendre le contexte

4. **Modifier**
   - Appliquer les patterns
   - Vérifier checklist CODING_RULES.md

5. **Mettre à jour docs (si nécessaire)**
   - Consulter MAINTENANCE_GUIDE.md
   - MAJ REFERENCE ou CODING_RULES

---

## 🚨 RÈGLES ABSOLUES

### TOUJOURS faire

✅ Lire REFERENCE_COMPLETE.md EN PREMIER
✅ Consulter CODING_RULES.md avant d'écrire du code
✅ Vérifier la checklist avant commit
✅ Mettre à jour les docs après changement significatif

### JAMAIS faire

❌ Chercher le code sans lire REFERENCE_COMPLETE.md d'abord
❌ Modifier du code sans consulter CODING_RULES.md
❌ Hardcoder `Path("projects")` (utiliser `get_project_path()`)
❌ Raise exception dans générateur SSE (yield error + return)
❌ Importer depuis racine (utiliser `lib/`)
❌ Laisser les docs obsolètes après modification

---

## 📊 CHECKLIST CLAUDE (AVANT CHAQUE TÂCHE)

```markdown
- [ ] J'ai lu REFERENCE_COMPLETE.md pour localiser le code
- [ ] J'ai identifié fichier:lignes exacts
- [ ] J'ai lu CODING_RULES.md pour les patterns applicables
- [ ] J'ai lu le code source aux lignes identifiées
- [ ] Je connais les règles critiques à respecter
- [ ] Je suis prêt à modifier le code correctement
```

---

## 📊 CHECKLIST CLAUDE (APRÈS CHAQUE MODIFICATION)

```markdown
- [ ] Mon code respecte TOUS les patterns de CODING_RULES.md
- [ ] J'ai vérifié la checklist "Avant commit"
- [ ] Aucun `Path("projects")` hardcodé
- [ ] Aucun `raise` dans générateur SSE
- [ ] Imports depuis `lib/` en priorité
- [ ] Si changement significatif : docs mises à jour
```

---

## 🎯 BÉNÉFICES ATTENDUS

| Métrique | Avant docs | Après docs | Gain |
|----------|-----------|------------|------|
| Temps localisation code | 5-10 min | 10 sec | **98%** |
| Erreurs de pattern | 5-10/tâche | 0-1/tâche | **90%** |
| Code cohérent | 60% | 100% | **40%** |
| Confiance réponses | 70% | 95% | **25%** |

---

## 💡 EXEMPLE CONCRET

### Tâche: "Ajoute une route pour exporter les résultats en PDF"

#### ❌ SANS les docs (ancien workflow)

1. Cherche "export" dans tout le projet (5 min)
2. Trouve 3-4 fichiers candidats
3. Lit `matching_engine.py` en entier (58KB)
4. Devine comment faire une route API
5. Hardcode `Path("projects")` (BUG)
6. Raise exception dans générateur SSE si erreur (BUG)
7. Code en 20 min, 2 bugs à corriger

**Temps total: 25 min, 2 bugs**

---

#### ✅ AVEC les docs (nouveau workflow)

1. Lit REFERENCE_COMPLETE.md section "Exports" (30 sec)
   → Export CSV : `matching_engine.py:1350-1450`
   → Routes export : `api/routers/matching.py:210-290`

2. Lit CODING_RULES.md section "Route API" (1 min)
   → Pattern obligatoire avec `get_project_path()`
   → Validation existence fichier
   → Gestion erreurs

3. Lit le code source aux lignes exactes (2 min)
   → Comprend la logique export CSV
   → S'inspire pour PDF

4. Écrit la route en suivant le pattern (5 min)
   ```python
   @router.get("/matching/{id}/export/pdf")
   async def export_pdf(project_id: str, matching_id: str):
       pm = ProjectManager()
       project_path = pm.get_project_path(project_id)

       if not project_path:
           raise HTTPException(404, "Projet introuvable")

       matching_file = project_path / "matchings" / matching_id / "results.json"

       if not matching_file.exists():
           raise HTTPException(404, "Matching introuvable")

       # Logique PDF...
   ```

5. Vérifie checklist CODING_RULES.md (1 min)
   - [x] Utilise `get_project_path()` ✓
   - [x] Valide existence fichier ✓
   - [x] Gestion erreurs ✓

6. MAJ REFERENCE_COMPLETE.md section "API REST" (1 min)
   → Ajoute ligne `/matching/{id}/export/pdf`

**Temps total: 10 min, 0 bug**

**Gain: 60% temps, 100% bugs évités** 🚀

---

## 🆘 EN CAS DE PROBLÈME

### Si Claude ne suit pas les docs

**Rajouter dans le prompt système:**

```markdown
RÈGLE ABSOLUE :
1. TOUJOURS lire REFERENCE_COMPLETE.md EN PREMIER
2. TOUJOURS consulter CODING_RULES.md avant d'écrire du code
3. TOUJOURS vérifier la checklist avant de proposer une modification
4. TOUJOURS mettre à jour les docs après changement significatif

Ne JAMAIS skip ces étapes, même si tu penses connaître la réponse.
```

---

### Si les docs deviennent obsolètes

**Revue hebdomadaire (5 min):**
- Vérifier que tous les fichiers référencés existent
- Tester 2-3 commandes "Commandes utiles"
- Valider 1-2 diagnostics

**Voir:** `MAINTENANCE_GUIDE.md` pour le processus complet

---

## 📞 QUESTIONS FRÉQUENTES

**Q: Dois-je lire les 3 fichiers à chaque fois ?**
A: Non. REFERENCE + CODING_RULES avant code, MAINTENANCE seulement si changement significatif.

**Q: Et si je ne trouve pas dans REFERENCE_COMPLETE.md ?**
A: Alors le fichier doit être mis à jour. Ajoute l'info manquante après avoir trouvé.

**Q: Combien de temps prend la lecture des docs ?**
A: 1-2 min max. Le gain de temps sur la recherche/correction compense largement.

**Q: Que faire si les docs sont incorrects ?**
A: Corriger immédiatement et noter dans le commit.

---

## ✅ VALIDATION FINALE

**Ce système fonctionne si et seulement si :**

1. ✅ Les docs sont maintenus à jour (< 1 semaine décalage)
2. ✅ Claude les consulte SYSTÉMATIQUEMENT
3. ✅ Les patterns sont respectés à 100%
4. ✅ Les mises à jour sont faites immédiatement

**Si un seul point manque → le système se dégrade rapidement**

---

**🎯 OBJECTIF: Claude 10x plus efficace, 90% bugs en moins**
**📖 CE WORKFLOW EST OBLIGATOIRE**

---

_Guide créé le: 18 octobre 2025_
_À lire AVANT toute intervention sur le code_
