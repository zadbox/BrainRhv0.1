# Événements SSE (Server-Sent Events)

## Format général

Les événements SSE suivent le format standard:

```
event: <event_type>
data: <json_payload>

```

**Note:** Chaque événement se termine par une ligne vide.

## Événements pour `/cvs/parse/stream`

### 1. Progress Event

```
event: progress
data: {"event":"progress","step":"parsing","current":5,"total":10,"progress":0.5,"message":"Parsing CV 5/10"}

```

**Étapes possibles:**
- `extracting`: Extraction du texte des fichiers
- `parsing`: Parsing LLM des CVs

### 2. Result Event

```
event: result
data: {"event":"result","data":{"filename":"jean_dupont_cv.pdf","success":true,"data":{"cv":"jean_dupont_cv.pdf","identite":{"nom":"Dupont","prenom":"Jean"},"titre":"Développeur Full Stack"}}}

```

### 3. Done Event

```
event: done
data: {"event":"done","summary":{"success_count":9,"failed_count":1,"total":10,"timings":{"total":125.3}}}

```

### 4. Error Event

```
event: error
data: {"event":"error","code":"PARSING_FAILED","message":"Échec du parsing de 3 CVs","details":{"failed_files":["cv1.pdf","cv2.pdf","cv3.pdf"]}}

```

## Événements pour `/matching/run/stream`

### 1. Progress Event

```
event: progress
data: {"event":"progress","step":"must_have_filtering","current":15,"total":32,"progress":0.469,"message":"Filtrage must-have: 15/32 CVs"}

```

**Étapes possibles:**
- `must_have_filtering`: Filtrage des critères éliminatoires
- `embedding`: Calcul des embeddings et similarité
- `nice_have_detection`: Détection des nice-have manquants
- `reranking`: Re-ranking LLM du top N

### 2. Result Event (CV filtré)

```
event: result
data: {"event":"result","data":{"cv":"jean_dupont_cv.pdf","status":"filtered","reason":"Manque critère must-have: Minimum 5 ans d'expérience"}}

```

### 3. Result Event (CV scoré)

```
event: result
data: {"event":"result","data":{"cv":"marie_martin_cv.pdf","score_final":0.823,"score_base":0.85,"bonus_nice_have_multiplicateur":0.8574,"coefficient_qualite_experience":1.25}}

```

### 4. Done Event

```
event: done
data: {"event":"done","summary":{"results":[...],"metadata":{"total_cvs":32,"filtered_must_have":8,"top_reranked":10,"duree_totale_s":342.5}}}

```

## Exemple de consommation JavaScript (Frontend)

```javascript
const eventSource = new EventSource('/api/v1/matching/run/stream', {
  method: 'POST',
  body: JSON.stringify(matchingRequest)
});

eventSource.addEventListener('progress', (e) => {
  const data = JSON.parse(e.data);
  console.log(`Progression: ${data.current}/${data.total} (${data.step})`);
  updateProgressBar(data.progress);
});

eventSource.addEventListener('result', (e) => {
  const data = JSON.parse(e.data);
  console.log('Résultat intermédiaire:', data.data);
  appendResult(data.data);
});

eventSource.addEventListener('done', (e) => {
  const data = JSON.parse(e.data);
  console.log('Matching terminé:', data.summary);
  eventSource.close();
  displayFinalResults(data.summary);
});

eventSource.addEventListener('error', (e) => {
  const data = JSON.parse(e.data);
  console.error('Erreur:', data.message);
  eventSource.close();
  showError(data.message);
});

eventSource.onerror = (error) => {
  console.error('SSE connection error:', error);
  eventSource.close();
};
```

## Bonnes pratiques

1. **Toujours fermer la connexion SSE** après l'événement `done` ou `error`
2. **Gérer les reconnexions** en cas d'erreur réseau (les navigateurs le font automatiquement par défaut)
3. **Afficher la progression en temps réel** pour améliorer l'UX sur les traitements longs
4. **Buffer les résultats intermédiaires** si le traitement est plus rapide que le rendu UI
5. **Timeout côté client** si aucun événement n'est reçu pendant >5 minutes
