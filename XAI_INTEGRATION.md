# Intégration xAI (Grok) - Documentation

## Résumé

xAI (Grok-4-fast-reasoning) a été intégré comme alternative à OpenAI pour le reranking LLM, avec bascule via configuration.

## Configuration

### 1. Variable d'environnement

```bash
export XAI_API_KEY="<YOUR_XAI_API_KEY>"
```

### 2. Fichier config.yaml

```yaml
llm:
  # Provider pour le reranking LLM
  reranking_provider: "openai"  # "openai" ou "xai" (Grok)

scoring:
  # Provider pour le reranking (copie pour compatibilité)
  reranking_provider: "openai"  # "openai" ou "xai" (Grok)
```

**Pour basculer vers xAI/Grok :**
```yaml
reranking_provider: "xai"
```

**Pour revenir à OpenAI :**
```yaml
reranking_provider: "openai"
```

## Modifications apportées

### 1. `matching_engine.py` (lignes 7-20)

**Nouveaux imports :**
```python
import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
```

### 1.1. `matching_engine.py` (lignes 57-61)

**Initialisation des températures dans `__init__()` :**
```python
# Températures pour les différents usages
# NOTE: Ces températures sont utilisées UNIQUEMENT pour xAI (Grok) et l'extraction
# GPT-5 mini ne supporte PAS le paramètre temperature (erreur 400 si fourni)
self.temperature_extraction = self.config.get("llm", {}).get("temperature_extraction", 0.1)
self.temperature_reranking = self.config.get("llm", {}).get("temperature_reranking", 0.2)  # Pour xAI uniquement
```

**Fix :** Résout `AttributeError: 'MatchingEngine' object has no attribute 'temperature_reranking'` lors de l'utilisation de xAI.

**Important :**
- ✅ `_rerank_with_xai()` utilise `temperature: self.temperature_reranking`
- ❌ `_rerank_with_openai()` n'utilise PAS de paramètre temperature (GPT-5 mini ne le supporte pas)

### 2. `matching_engine.py` (lignes 1045-1121)

**Routing provider dans `rerank_with_llm()` :**
```python
# === ROUTING PROVIDER ===
provider = self.scoring_config.get("reranking_provider", "openai").lower()
print(f"🔀 Provider reranking: {provider}")

try:
    if provider == "xai":
        return self._rerank_with_xai(...)
    else:  # default: openai
        return self._rerank_with_openai(...)

except Exception as e:
    # === FALLBACK (préserve les données de base) ===
    ...
```

### 3. Nouvelles méthodes

#### `_rerank_with_openai()` (lignes 1123-1164)
- Code OpenAI extrait de `rerank_with_llm()`
- Gère l'appel API OpenAI
- Enrichit les résultats avec evidences/flags

#### `_call_xai_with_retry()` (lignes 1166-1196)
- Appel API xAI avec retry automatique (tenacity)
- 3 tentatives max
- Exponential backoff (2s min, 10s max)
- Timeout 90s
- Retry sur erreurs réseau et timeouts

#### `_rerank_with_xai()` (lignes 1198-1253)
- Appel API xAI (format OpenAI-compatible)
- Modèle : `grok-4-fast-reasoning`
- Même prompt et logique qu'OpenAI
- Enrichit les résultats (idem OpenAI)

### 4. `requirements.txt`

**Nouvelle dépendance :**
```
tenacity>=8.2.0
```

### 5. `config_loader.py` (lignes 94-99)

**Validation de la clé xAI au chargement de la config :**
```python
# Vérifier xAI si provider configuré sur "xai"
reranking_provider = self.get("llm.reranking_provider", "openai")
if reranking_provider == "xai":
    if not os.getenv("XAI_API_KEY"):
        print(f"⚠️ reranking_provider='xai' mais XAI_API_KEY manquante dans l'environnement")
        print("Définissez export XAI_API_KEY='xai-...' ou changez reranking_provider='openai'")
```

**Bénéfice :** Avertissement immédiat au démarrage si la configuration xAI est activée sans la clé API.

## Architecture

```
rerank_with_llm()
    ├─ Préparation des CVs (cv_summaries, prompt)
    │
    ├─ ROUTING
    │   ├─ provider == "xai"
    │   │   └─> _rerank_with_xai()
    │   │        └─> _call_xai_with_retry()  (retry 3x)
    │   │             └─> API xAI (Grok)
    │   │
    │   └─ provider == "openai" (default)
    │       └─> _rerank_with_openai()
    │            └─> OpenAI client
    │                 └─> API OpenAI (GPT-5-mini)
    │
    └─ FALLBACK (si exception)
        └─> Tri par score_final
            └─> Messages explicites
            └─> Flags auto-détectés
```

## API xAI

### Endpoint
```
https://api.x.ai/v1/chat/completions
```

### Format requête
```json
{
  "model": "grok-4-fast-reasoning",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "response_format": {"type": "json_object"},
  "temperature": 0.2,
  "max_tokens": 1200,
  "stream": false
}
```

### Format réponse (OpenAI-compatible)
```json
{
  "choices": [
    {
      "message": {
        "content": "{\"ranked_cvs\": [...]}"
      }
    }
  ]
}
```

## Tests

### Test 1 : Import et structure
```bash
cd "/Users/houssam/Downloads/Brain RH migration"
python3 -c "from matching_engine import MatchingEngine; engine = MatchingEngine(); print(engine.scoring_config.get('reranking_provider'))"
```

**Résultat attendu :** `openai`

### Test 2 : Bascule vers xAI
```bash
# 1. Modifier config.yaml
sed -i '' 's/reranking_provider: "openai"/reranking_provider: "xai"/g' config.yaml

# 2. Exporter la clé
export XAI_API_KEY="<YOUR_XAI_API_KEY>"

# 3. Relancer backend
uvicorn api.main:app --reload --port 8000

# 4. Lancer un matching depuis l'UI
# Observer les logs : "🔀 Provider reranking: xai"
```

### Test 3 : Retour à OpenAI
```bash
# 1. Modifier config.yaml
sed -i '' 's/reranking_provider: "xai"/reranking_provider: "openai"/g' config.yaml

# 2. Relancer backend
# Observer les logs : "🔀 Provider reranking: openai"
```

## Comportement en cas d'erreur

### Erreur xAI (timeout, 429, 5xx)
1. **Retry automatique** : 3 tentatives avec exponential backoff
2. **Si échec après 3 tentatives** : Fallback
3. **Fallback** : Tri par score_final + messages explicites

### Erreur OpenAI
1. **Fallback immédiat** : Tri par score_final + messages explicites

### Messages fallback
```
⚠️ Re-ranking LLM indisponible (erreur: Connection error).
Score base: 0.850, Bonus nice-have: 0.950, Score final: 0.808.
Tri automatique par score final (coefficient neutre appliqué).
```

## Notes importantes

1. **Prompts identiques** : xAI et OpenAI reçoivent exactement le même prompt
2. **Schéma JSON identique** : Format de réponse unifié
3. **Evidences/flags** : Supportés par les deux providers
4. **Coefficient qualité** : Calculé de la même manière
5. **Fallback robuste** : Préserve les scores de base en cas d'erreur

## Compatibilité

- ✅ Anciens matchings (sans xAI) : Fonctionnent toujours
- ✅ Fallback : Compatible avec les deux providers
- ✅ API historique : Charge correctement les résultats xAI/OpenAI
- ✅ Frontend : Affiche les résultats des deux providers de manière identique

## Rollback

Pour désactiver xAI et revenir à OpenAI uniquement :

```yaml
# config.yaml
reranking_provider: "openai"
```

Puis redémarrer le backend. Aucune autre modification nécessaire.

## Monitoring

**Logs à surveiller :**
- `🔀 Provider reranking: xai` → xAI actif
- `🔀 Provider reranking: openai` → OpenAI actif
- `✅ Re-ranking xAI (Grok): N CVs retournés` → Succès xAI
- `✅ Re-ranking OpenAI: N CVs retournés` → Succès OpenAI
- `❌ Exception rerank: ... → fallback` → Erreur (fallback déclenché)

## Performance

**xAI vs OpenAI :**
- Timeout : 90s (identique)
- Retry : 3x pour xAI, 0x pour OpenAI
- Latence typique : ~5-10s (selon charge réseau)

## Support

En cas de problème :
1. Vérifier `XAI_API_KEY` dans l'environnement
2. Vérifier `reranking_provider` dans `config.yaml`
3. Consulter les logs backend (`uvicorn`)
4. Tester avec `provider: "openai"` pour isoler le problème

---

**Date d'intégration** : 2025-01-22
**Version** : 1.0
**Status** : ✅ Opérationnel
